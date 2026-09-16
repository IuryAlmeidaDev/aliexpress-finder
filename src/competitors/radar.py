import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from src.competitors.models import CompetitorProduct
from src.competitors.extractors.base import BaseExtractor

class CompetitorRadar:
    """Discovers direct competitors in the domestic market (Mercado Livre and web)."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def find_competitors(self, query: str, limit: int = 5) -> List[CompetitorProduct]:
        """Queries Mercado Livre for competitors matching the query."""
        formatted_query = query.strip().replace(" ", "-")
        url = f"https://lista.mercadolivre.com.br/{formatted_query}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                return self.parse_search_html(resp.text, limit=limit)
        except Exception:
            pass

        return []

    def parse_search_html(self, html: str, limit: int = 5) -> List[CompetitorProduct]:
        """Parses Mercado Livre search HTML and extracts structured competitor data."""
        soup = BeautifulSoup(html, "html.parser")
        competitors: List[CompetitorProduct] = []

        # Items are usually in <li class="ui-search-layout__item">
        items = soup.find_all("li", class_=re.compile(r"ui-search-layout__item"))
        if not items:
            items = soup.find_all("div", class_=re.compile(r"ui-search-result"))

        for item in items:
            if len(competitors) >= limit:
                break

            # Title & Link
            link_tag = item.find("a", class_=re.compile(r"ui-search-link|ui-search-item__group__element"))
            if not link_tag:
                continue
            
            url = link_tag.get("href", "")
            title_tag = item.find(re.compile(r"h2|span"), class_=re.compile(r"ui-search-item__title"))
            title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
            if not title:
                continue

            # Price
            price = self._extract_item_price(item)
            if price <= 0:
                continue

            # Seller / Store name
            seller_tag = item.find(class_=re.compile(r"seller-info|brand-discoverability|ui-search-item__group__element--seller"))
            store_name = seller_tag.get_text(strip=True) if seller_tag else "Mercado Livre Seller"

            # Shipping (Full, Frete Grátis)
            shipping_type = "Normal"
            item_text = item.get_text()
            if "FULL" in item_text or item.find(class_=re.compile(r"fulfillment")):
                shipping_type = "Full"
            elif "frete grátis" in item_text.lower() or item.find(class_=re.compile(r"shipping--free")):
                shipping_type = "Frete Grátis"

            # Rating and Reviews
            rating = None
            reviews_count = None
            rating_tag = item.find(class_=re.compile(r"rating-number"))
            if rating_tag:
                try:
                    rating = float(rating_tag.get_text(strip=True).replace(",", "."))
                except ValueError:
                    pass

            reviews_tag = item.find(class_=re.compile(r"reviews__amount"))
            if reviews_tag:
                clean_rev = re.sub(r"[^\d]", "", reviews_tag.get_text())
                if clean_rev:
                    reviews_count = int(clean_rev)

            # Differentials & Kit detection
            kit_items = BaseExtractor.detect_kit_items(title)
            differentials = []
            if shipping_type == "Full":
                differentials.append("Entrega Full")
            elif shipping_type == "Frete Grátis":
                differentials.append("Frete Grátis")

            for kw in ["uv400", "safira", "aço", "couro", "bluetooth", "garantia", "prova d'água", "resistente"]:
                if kw in title.lower():
                    differentials.append(kw.title())

            competitor = CompetitorProduct(
                title=title,
                url=url,
                store_name=store_name,
                platform="Mercado Livre",
                price_brl=price,
                shipping_type=shipping_type,
                rating=rating,
                reviews_count=reviews_count,
                kit_items=kit_items,
                differentials=differentials
            )
            competitors.append(competitor)

        return competitors

    def _extract_item_price(self, item: BeautifulSoup) -> float:
        # Search price section
        price_wrapper = item.find(class_=re.compile(r"ui-search-price__second-line|ui-search-price__part--medium"))
        target_scope = price_wrapper if price_wrapper else item

        fraction = target_scope.find(class_=re.compile(r"andes-money-amount__fraction"))
        if fraction:
            val_str = fraction.get_text(strip=True).replace(".", "").replace(",", ".")
            cents = target_scope.find(class_=re.compile(r"andes-money-amount__cents"))
            if cents:
                val_str = f"{val_str}.{cents.get_text(strip=True)}"
            try:
                return float(val_str)
            except ValueError:
                pass

        return 0.0
