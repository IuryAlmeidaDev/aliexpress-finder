from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .brand import analyze_brand_potential, normalize
from .client import MercadoLivreClient, MercadoLivreError
from .models import RadarProduct, RadarScore
from .reporting import export_radar_report, report_filename
from .repository import RadarRepository
from .scoring import score_product


ALLOWED_ROOT_TERMS = (
    "casa", "moveis", "decoracao", "papelaria", "armarinho", "ferramentas",
    "esportes", "moda", "brinquedos", "hobbies",
)
BLOCKED_TERMS = (
    "alimentos", "bebidas", "saude", "medicamentos", "hospitalar", "armas",
    "fumantes", "adultos", "animais vivos", "agroquim", "pneus", "baterias",
)


@dataclass
class RadarRunResult:
    run_id: str
    status: str
    report_path: Optional[str]
    products: int
    opportunities: int
    errors: list[str] = field(default_factory=list)


class MercadoLivreRadar:
    def __init__(
        self,
        client: MercadoLivreClient,
        repository: RadarRepository,
        report_dir: str,
        max_categories: int = 30,
        max_candidates: int = 100,
        review_limit: int = 20,
    ):
        self.client = client
        self.repository = repository
        self.report_dir = report_dir
        self.max_categories = max_categories
        self.max_candidates = max_candidates
        self.review_limit = review_limit

    @staticmethod
    def _eligible(name: str) -> bool:
        value = normalize(name)
        return not any(term in value for term in BLOCKED_TERMS)

    def discover_categories(self) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        queue = [
            category for category in self.client.root_categories()
            if any(term in normalize(str(category.get("name", ""))) for term in ALLOWED_ROOT_TERMS)
            and self._eligible(str(category.get("name", "")))
        ]
        leaves: list[str] = []
        seen: set[str] = set()
        pool_limit = max(self.max_categories, self.max_categories * 3)
        while queue and len(leaves) < pool_limit:
            current = queue.pop(0)
            category_id = str(current.get("id") or "")
            if not category_id or category_id in seen:
                continue
            seen.add(category_id)
            try:
                details = self.client.category(category_id)
            except MercadoLivreError as exc:
                errors.append(str(exc))
                continue
            children = [
                child for child in details.get("children_categories") or []
                if self._eligible(str(child.get("name", "")))
            ]
            if children:
                queue.extend(children)
            else:
                leaves.append(category_id)
        return leaves, errors

    def run(self, mode: str = "manual", category_ids: Optional[list[str]] = None) -> RadarRunResult:
        now = datetime.now(timezone.utc)
        run_id = uuid.uuid4().hex
        config = {
            "max_categories": self.max_categories,
            "max_candidates": self.max_candidates,
            "review_limit": self.review_limit,
            "category_ids": category_ids or [],
        }
        errors: list[str] = []
        try:
            self.repository.start_run(run_id, mode, config, now)
        except Exception as exc:
            return RadarRunResult(run_id, "failed", None, 0, 0, [str(exc)])
        try:
            self.client.validate_configuration()
            categories = category_ids or []
            if not categories:
                candidates, discovery_errors = self.discover_categories()
                errors.extend(discovery_errors)
                categories = self.repository.choose_categories(candidates, self.max_categories)
            if not categories:
                raise MercadoLivreError("Nenhuma categoria elegível foi descoberta.")
            categories = categories[: self.max_categories]
            self.repository.mark_categories_visited(categories, now)

            products: list[RadarProduct] = []
            identities: set[str] = set()
            for category_id in categories:
                if len(products) >= self.max_candidates:
                    break
                try:
                    highlights = self.client.highlights(category_id)
                except MercadoLivreError as exc:
                    errors.append(str(exc))
                    continue
                for entry in highlights:
                    if len(products) >= self.max_candidates:
                        break
                    try:
                        product = self.client.resolve_highlight(entry, category_id)
                        stable_key = product.catalog_product_id or product.entity_key
                        if stable_key in identities:
                            continue
                        identities.add(stable_key)
                        try:
                            self.client.add_reviews(product, self.review_limit)
                        except MercadoLivreError as exc:
                            errors.append(f"{product.entity_key}: {exc}")
                        products.append(product)
                    except MercadoLivreError as exc:
                        errors.append(str(exc))

            if not products:
                raise MercadoLivreError("Nenhum produto pôde ser enriquecido nas categorias consultadas.")

            for product in products:
                self.repository.save_observation(run_id, product, now)

            category_groups: dict[str, list[RadarProduct]] = {}
            for product in products:
                category_groups.setdefault(product.category_id, []).append(product)
            scored: list[tuple[RadarProduct, RadarScore]] = []
            for product in products:
                group = category_groups[product.category_id]
                counts = [p.review_count for p in group if p.review_count is not None]
                ratings = [p.review_average for p in group if p.review_average is not None]
                previous = self.repository.previous_observation(product, now)
                evidence = analyze_brand_potential(product)
                score = score_product(
                    product,
                    evidence,
                    max(counts) if counts else None,
                    statistics.mean(ratings) if ratings else None,
                    previous,
                )
                self.repository.save_score(run_id, product, score)
                scored.append((product, score))

            scored.sort(key=lambda pair: (pair[1].combined_score, pair[1].brand_coverage), reverse=True)
            # Diversidade: no máximo cinco prioridades por categoria.
            category_counts: dict[str, int] = {}
            priority_count = 0
            for product, score in scored:
                if score.priority:
                    category_counts[product.category_id] = category_counts.get(product.category_id, 0) + 1
                    priority_count += 1
                    if category_counts[product.category_id] > 5 or priority_count > 30:
                        score.priority = False
            status = "partial" if errors else "success"
            run_info = {
                "ID": run_id,
                "Início UTC": now.isoformat(),
                "Modo": mode,
                "Status": status,
                "Categorias": len(categories),
                "Produtos": len(products),
                "Erros": " | ".join(errors),
                "Versão das regras": "1",
            }
            path = report_filename(self.report_dir, run_id, now)
            export_radar_report(scored, run_info, path)
            self.repository.finish_run(run_id, status, errors, datetime.now(timezone.utc))
            return RadarRunResult(
                run_id, status, path, len(products), sum(1 for _, score in scored if score.priority), errors
            )
        except Exception as exc:
            errors.append(str(exc))
            self.repository.finish_run(run_id, "failed", errors, datetime.now(timezone.utc))
            return RadarRunResult(run_id, "failed", None, 0, 0, errors)
