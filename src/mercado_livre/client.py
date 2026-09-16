from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

import requests

from .models import RadarProduct


class MercadoLivreError(RuntimeError):
    pass


class MercadoLivreAuthError(MercadoLivreError):
    pass


class MercadoLivreClient:
    BASE_URL = "https://api.mercadolibre.com"

    def __init__(
        self,
        access_token: str,
        site_id: str = "MLB",
        session: Optional[requests.Session] = None,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 20.0,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
        token_file: str = "",
    ):
        self.access_token = access_token.strip()
        self.site_id = site_id
        self.session = session or requests.Session()
        self.sleep = sleep
        self.timeout = timeout
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.refresh_token = refresh_token.strip()
        self.token_file = Path(token_file) if token_file else None
        self._load_tokens()

    def _load_tokens(self) -> None:
        if not self.token_file or not self.token_file.exists():
            return
        try:
            payload = json.loads(self.token_file.read_text(encoding="utf-8"))
            self.access_token = str(payload.get("access_token") or self.access_token)
            self.refresh_token = str(payload.get("refresh_token") or self.refresh_token)
        except (OSError, ValueError, TypeError):
            pass

    def _save_tokens(self) -> None:
        if not self.token_file:
            return
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.token_file.with_suffix(self.token_file.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"access_token": self.access_token, "refresh_token": self.refresh_token}),
            encoding="utf-8",
        )
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, self.token_file)

    def _refresh_access_token(self) -> bool:
        if not (self.client_id and self.client_secret and self.refresh_token):
            return False
        try:
            response = self.session.post(
                f"{self.BASE_URL}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return False
        access_token = str(payload.get("access_token") or "")
        if not access_token:
            return False
        self.access_token = access_token
        self.refresh_token = str(payload.get("refresh_token") or self.refresh_token)
        self._save_tokens()
        return True

    def validate_configuration(self) -> None:
        if not self.access_token and not self._refresh_access_token():
            raise MercadoLivreAuthError(
                "Credenciais do Mercado Livre não configuradas. Autorize uma aplicação e "
                "informe o access token ou client ID, client secret e refresh token."
            )

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        self.validate_configuration()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        last_error: Optional[Exception] = None
        refreshed = False
        for attempt in range(3):
            try:
                response = self.session.get(
                    f"{self.BASE_URL}{path}", headers=headers, params=params, timeout=self.timeout
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt < 2:
                    self.sleep(2**attempt)
                    continue
                raise MercadoLivreError(f"Falha de rede ao consultar {path}: {exc}") from exc

            if response.status_code == 401:
                if not refreshed and self._refresh_access_token():
                    refreshed = True
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    continue
                raise MercadoLivreAuthError("Token do Mercado Livre inválido, expirado ou revogado.")
            if response.status_code == 403:
                raise MercadoLivreAuthError(f"Acesso negado pelo Mercado Livre em {path}.")
            if response.status_code == 429:
                if attempt < 2:
                    wait = min(float(response.headers.get("Retry-After", 2**attempt)), 30.0)
                    self.sleep(wait)
                    continue
            if 500 <= response.status_code < 600 and attempt < 2:
                self.sleep(2**attempt)
                continue
            if response.status_code == 404:
                raise MercadoLivreError(f"Recurso não encontrado: {path}")
            try:
                response.raise_for_status()
            except requests.RequestException as exc:
                raise MercadoLivreError(f"Erro HTTP {response.status_code} em {path}") from exc
            return response.json()
        raise MercadoLivreError(f"Não foi possível consultar {path}: {last_error or 'limite de chamadas'}")

    def root_categories(self) -> list[dict[str, Any]]:
        data = self._get(f"/sites/{self.site_id}/categories")
        return list(data or [])

    def category(self, category_id: str) -> dict[str, Any]:
        return dict(self._get(f"/categories/{category_id}") or {})

    def highlights(self, category_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/highlights/{self.site_id}/category/{category_id}")
        return list(data.get("content", []))

    @staticmethod
    def _attributes(data: dict[str, Any]) -> dict[str, str]:
        result: dict[str, str] = {}
        for attribute in data.get("attributes") or []:
            key = attribute.get("id") or attribute.get("name")
            value = attribute.get("value_name")
            if value is None and attribute.get("values"):
                value = attribute["values"][0].get("name")
            if key and value is not None:
                result[str(key)] = str(value)
        return result

    def resolve_highlight(self, entry: dict[str, Any], category_id: str) -> RadarProduct:
        entity_id = str(entry.get("id") or "")
        entity_type = str(entry.get("type") or "").upper()
        rank = entry.get("position")
        if not entity_id or entity_type not in {"ITEM", "PRODUCT", "USER_PRODUCT"}:
            raise MercadoLivreError(f"Destaque com identidade não suportada: {entry!r}")

        if entity_type == "ITEM":
            data = self._get(f"/items/{entity_id}")
        elif entity_type == "PRODUCT":
            data = self._get(f"/products/{entity_id}")
        else:
            data = self._get(f"/user-products/{entity_id}")

        buy_box = data.get("buy_box_winner") or data.get("buy_box_winner_data") or {}
        item_id = data.get("item_id") or buy_box.get("item_id") or buy_box.get("id")
        catalog_id = data.get("catalog_product_id") or (entity_id if entity_type == "PRODUCT" else None)
        title = data.get("name") or data.get("title") or data.get("family_name") or entity_id
        url = data.get("permalink") or data.get("url") or buy_box.get("permalink") or ""
        price = data.get("price")
        if price is None:
            price = buy_box.get("price")
        return RadarProduct(
            entity_id=entity_id,
            entity_type=entity_type,
            category_id=str(data.get("category_id") or category_id),
            title=str(title),
            url=str(url),
            rank=int(rank) if rank is not None else None,
            catalog_product_id=str(catalog_id) if catalog_id else None,
            item_id=str(item_id or entity_id) if (item_id or entity_type == "ITEM") else None,
            price=float(price) if price is not None else None,
            sold_quantity=data.get("sold_quantity"),
            attributes=self._attributes(data),
            raw=data,
        )

    def add_reviews(self, product: RadarProduct, limit: int = 20) -> RadarProduct:
        if not product.item_id:
            return product
        params: dict[str, Any] = {"limit": limit, "offset": 0}
        if product.catalog_product_id:
            params["catalog_product_id"] = product.catalog_product_id
        data = self._get(f"/reviews/item/{product.item_id}", params=params)
        paging = data.get("paging") or {}
        product.review_count = int(paging.get("total") or 0)
        average = data.get("rating_average")
        product.review_average = float(average) if average is not None else None
        product.review_texts = [
            str(review.get("content") or review.get("title") or "").strip()
            for review in data.get("reviews") or []
            if str(review.get("content") or review.get("title") or "").strip()
        ]
        return product
