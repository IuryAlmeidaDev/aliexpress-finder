import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from src.competitors.extractors.base import BaseExtractor
from src.competitors.models import TargetProduct

class UniversalWebExtractor(BaseExtractor):
    """Universal fallback extractor using JSON-LD, OpenGraph, and standard meta tags."""

    def can_handle(self, url: str) -> bool:
        # Fallback extractor handles any URL
        return True

    def extract(self, url: str, html: str) -> TargetProduct:
        soup = BeautifulSoup(html, "html.parser")
        
        json_ld_data = self._find_product_jsonld(soup)
        
        title = self._extract_title(soup, json_ld_data)
        price = self._extract_price(soup, json_ld_data)
        description = self._extract_description(soup, json_ld_data)
        
        full_text = f"{title} {description}"
        kit_items = self.detect_kit_items(full_text)
        clean_query = self.clean_title(title)
        
        return TargetProduct(
            title=title,
            reference_price_brl=price,
            clean_query=clean_query,
            url=url,
            category="E-Commerce",
            specs={},
            kit_items=kit_items
        )

    def _find_product_jsonld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "Product":
                        return data
                    # Check @graph
                    if "@graph" in data and isinstance(data["@graph"], list):
                        for item in data["@graph"]:
                            if isinstance(item, dict) and item.get("@type") == "Product":
                                return item
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            return item
            except (json.JSONDecodeError, TypeError):
                continue
        return {}

    def _extract_title(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> str:
        if json_ld and json_ld.get("name"):
            return str(json_ld["name"]).strip()

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content"):
            return meta_title["content"].strip()

        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            # Remove site name suffix like " - Loja XYZ" or " | Brand"
            title_text = re.sub(r"(\s*[\-\|]\s*[^-\|]+)$", "", title_text)
            if title_text:
                return title_text

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return "Produto Desconhecido"

    def _extract_price(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> float:
        # Check JSON-LD
        if json_ld:
            offers = json_ld.get("offers")
            if isinstance(offers, dict) and "price" in offers:
                try:
                    return float(offers["price"])
                except (ValueError, TypeError):
                    pass
            elif isinstance(offers, list) and offers and "price" in offers[0]:
                try:
                    return float(offers[0]["price"])
                except (ValueError, TypeError):
                    pass

        # Check OpenGraph / Product price tags
        for prop in ["product:price:amount", "og:price:amount", "price"]:
            meta_price = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if meta_price and meta_price.get("content"):
                try:
                    cleaned_val = meta_price["content"].replace(",", ".")
                    return float(cleaned_val)
                except ValueError:
                    pass

        # Check text search for R$ xx.xx
        text = soup.get_text()
        m = re.search(r"R\$\s*([\d\.,]+)", text)
        if m:
            val_str = m.group(1).replace(".", "").replace(",", ".")
            try:
                return float(val_str)
            except ValueError:
                pass

        return 0.0

    def _extract_description(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> str:
        if json_ld and json_ld.get("description"):
            return str(json_ld["description"])

        og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if og_desc and og_desc.get("content"):
            return og_desc["content"]

        return ""
