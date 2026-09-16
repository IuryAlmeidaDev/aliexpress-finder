from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .models import RadarProduct, RadarScore


def _record(product: RadarProduct, score: RadarScore) -> dict[str, Any]:
    return {
        "Produto": product.title,
        "Categoria": product.category_id,
        "Tipo": product.entity_type,
        "ID": product.entity_id,
        "Posição bestseller": product.rank,
        "Preço observado (R$)": product.price,
        "Avaliações": product.review_count,
        "Nota média": product.review_average,
        "Demanda (0-100)": score.demand_score,
        "Cobertura demanda (%)": score.demand_coverage,
        "Potencial de marca (0-100)": score.brand_score,
        "Cobertura marca (%)": score.brand_coverage,
        "Prioridade combinada": score.combined_score,
        "Evidências de demanda": " | ".join(score.demand_reasons),
        "Hipóteses de diferenciação": " | ".join(score.brand_reasons),
        "Contrapontos": " | ".join(score.counterpoints),
        "Link": product.url,
    }


def export_radar_report(
    scored: list[tuple[RadarProduct, RadarScore]],
    run: dict[str, Any],
    filepath: str,
) -> str:
    destination = Path(filepath)
    destination.parent.mkdir(parents=True, exist_ok=True)
    priority = [_record(p, s) for p, s in scored if s.priority]
    investigate = [_record(p, s) for p, s in scored if not s.priority]
    evidence = []
    for product, score in scored:
        for kind, values in (
            ("demanda", score.demand_reasons),
            ("marca", score.brand_reasons),
            ("contraponto", score.counterpoints),
        ):
            evidence.extend({"ID": product.entity_id, "Tipo": kind, "Evidência": value} for value in values)

    handle, temp_name = tempfile.mkstemp(suffix=".xlsx", dir=str(destination.parent))
    os.close(handle)
    try:
        with pd.ExcelWriter(temp_name, engine="openpyxl") as writer:
            pd.DataFrame(priority).to_excel(writer, sheet_name="Oportunidades", index=False)
            pd.DataFrame(investigate).to_excel(writer, sheet_name="Investigar", index=False)
            pd.DataFrame(evidence).to_excel(writer, sheet_name="Evidências", index=False)
            pd.DataFrame([run]).to_excel(writer, sheet_name="Execução", index=False)
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return str(destination)


def report_filename(report_dir: str, run_id: str, now: datetime) -> str:
    stamp = now.strftime("%Y%m%d-%H%M%S")
    return str(Path(report_dir) / f"radar_mercado_livre_{stamp}_{run_id[:8]}.xlsx")
