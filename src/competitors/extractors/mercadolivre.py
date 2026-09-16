import re
import json
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from src.competitors.extractors.base import BaseExtractor
from src.competitors.models import TargetProduct

class MercadoLivreExtractor(BaseExtractor):
    """Specialized extractor for Mercado Livre product pages."""

    def can_handle(self, url: str) -> bool:
        lower_url = url.lower()
        return "mercadolivre.com" in lower_url or "mercadolibre.com" in lower_url

    def extract(self, url: str, html: str) -> TargetProduct:
        soup = BeautifulSoup(html, "html.parser")
        
        title = self._extract_title(soup, url)
        price = self._extract_price(soup)
        description = self._extract_description(soup)
        
        full_text = f"{title} {description}"
        kit_items = self.detect_kit_items(full_text)
        clean_query = self.clean_title(title)
        
        specs = self._extract_specs(soup)

        return TargetProduct(
            title=title,
            reference_price_brl=price,
            clean_query=clean_query,
            url=url,
            category="Mercado Livre",
            specs=specs,
            kit_items=kit_items
        )

    def _extract_title(self, soup: BeautifulSoup, url: str = "") -> str:
        # 1. Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            raw_title = og_title["content"].strip()
            raw_title = re.sub(r"-\s*R\$\s*[\d\.,]+.*$", "", raw_title)
            raw_title = re.sub(r"\|\s*Mercado\s*Livre.*$", "", raw_title, flags=re.IGNORECASE).strip()
            if raw_title and "mercado livre" not in raw_title.lower() and "mercado libre" not in raw_title.lower():
                return raw_title

        # 2. Try JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("name"):
                    name = str(data["name"]).strip()
                    if name and "mercado libre" not in name.lower():
                        return name
            except (json.JSONDecodeError, TypeError):
                continue

        # 3. Try h1
        h1 = soup.find("h1")
        if h1:
            h1_text = h1.get_text(strip=True)
            if h1_text and "mercado libre" not in h1_text.lower():
                return h1_text

        # 4. Fallback: Extract from URL slug (e.g. /MLB-123456-nome-do-produto-_JM)
        if url:
            m = re.search(r"MLB-?\d+-([^/?#]+)", url)
            if m:
                slug = m.group(1).replace("-", " ").replace("_JM", "").strip().title()
                if slug:
                    return slug

        return "Produto Mercado Livre"

    def _extract_price(self, soup: BeautifulSoup) -> float:
        # 1. Try JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    offers = data.get("offers")
                    if isinstance(offers, dict) and "price" in offers:
                        return float(offers["price"])
                    elif isinstance(offers, list) and offers and "price" in offers[0]:
                        return float(offers[0]["price"])
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        # 2. Try meta og:title with price: e.g. "Produto - R$ 58,11"
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            m = re.search(r"R\$\s*([\d\.,]+)", og_title["content"])
            if m:
                val = m.group(1).replace(".", "").replace(",", ".")
                try:
                    return float(val)
                except ValueError:
                    pass

        # 3. Try standard ML price elements
        fraction = soup.find(class_=re.compile(r"andes-money-amount__fraction|price-tag-fraction"))
        if fraction:
            val_str = fraction.get_text(strip=True).replace(".", "").replace(",", ".")
            cents = soup.find(class_=re.compile(r"andes-money-amount__cents|price-tag-cents"))
            if cents:
                val_str = f"{val_str}.{cents.get_text(strip=True)}"
            try:
                return float(val_str)
            except ValueError:
                pass

        return 0.0

    def _extract_description(self, soup: BeautifulSoup) -> str:
        og_desc = soup.find("meta", property=re.compile(r"og:description|twitter:description"))
        if og_desc and og_desc.get("content"):
            return og_desc["content"]
        return ""

    def _extract_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        specs = {}
        rows = soup.find_all("tr")
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True).lower()
                val = td.get_text(strip=True)
                specs[key] = val
        return specs
