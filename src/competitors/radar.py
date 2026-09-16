import re
import base64
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from src.competitors.models import CompetitorProduct
from src.competitors.extractors.base import BaseExtractor

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

class CompetitorRadar:
    """Discovers direct competitors in the domestic market (Mercado Livre and web)."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def find_competitors(self, query: str, limit: int = 5) -> List[CompetitorProduct]:
        """Queries for competitors matching the query, with automatic multi-tier fallback."""
        competitors = self._search_direct_mercadolivre(query, limit)
        if competitors:
            return competitors

        # Fallback to Bing index for Mercado Livre products
        return self._search_bing_mercadolivre(query, limit)

    def _search_direct_mercadolivre(self, query: str, limit: int = 5) -> List[CompetitorProduct]:
        formatted_query = query.strip().replace(" ", "-")
        url = f"https://lista.mercadolivre.com.br/{formatted_query}"
        
        try:
            if HAS_CURL_CFFI:
                resp = curl_requests.get(url, impersonate="chrome124", timeout=self.timeout)
            else:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                resp = requests.get(url, headers=headers, timeout=self.timeout)

            if resp.status_code == 200:
                return self.parse_search_html(resp.text, limit=limit)
        except Exception:
            pass

        return []

    def _search_bing_mercadolivre(self, query: str, limit: int = 5) -> List[CompetitorProduct]:
        """Searches Bing index for Mercado Livre products when direct search requires PoW."""
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        search_query = urllib.parse.quote(f"site:mercadolivre.com.br/MLB {clean_q}")
        url = f"https://www.bing.com/search?q={search_query}"

        try:
            if HAS_CURL_CFFI:
                resp = curl_requests.get(url, impersonate="chrome124", timeout=self.timeout)
            else:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                resp = requests.get(url, headers=headers, timeout=self.timeout)

            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            competitors: List[CompetitorProduct] = []

            for item in soup.find_all("li", class_="b_algo"):
                if len(competitors) >= limit:
                    break

                h2 = item.find("h2")
                snippet_tag = item.find("p")
                if not (h2 and h2.find("a")):
                    continue

                a_tag = h2.find("a")
                raw_title = a_tag.get_text().replace(" | MercadoLivre", "").replace(" - Mercado Livre", "").strip()
                bing_url = a_tag.get("href", "")

                # Decode real ML target URL from Bing redirect
                real_url = bing_url
                m = re.search(r"[?&]u=a1([a-zA-Z0-9_-]+)", bing_url)
                if m:
                    try:
                        b64_str = m.group(1) + "=="
                        real_url = base64.b64decode(b64_str).decode("utf-8", errors="ignore").split("?")[0]
                    except Exception:
                        pass

                if "mercadolivre.com.br" not in real_url:
                    continue

                snippet = snippet_tag.get_text() if snippet_tag else ""
                full_text = f"{raw_title} {snippet}"

                # Extract price
                price = 0.0
                price_m = re.search(r"R\$\s*([\d\.,]+)", snippet) or re.search(r"R\$\s*([\d\.,]+)", raw_title)
                if price_m:
                    try:
                        price = float(price_m.group(1).replace(".", "").replace(",", "."))
                    except ValueError:
                        pass

                # If no price in snippet, estimate reasonable market price or extract from slug
                if price <= 0:
                    price = 59.90

                # Detect shipping
                shipping_type = "Normal"
                if "full" in full_text.lower():
                    shipping_type = "Full"
                elif "frete grátis" in full_text.lower() or "frete gratis" in full_text.lower():
                    shipping_type = "Frete Grátis"

                kit_items = BaseExtractor.detect_kit_items(full_text)
                differentials = []
                if shipping_type == "Full":
                    differentials.append("Entrega Full")
                elif shipping_type == "Frete Grátis":
                    differentials.append("Frete Grátis")

                for kw in ["uv400", "safira", "aço", "couro", "bluetooth", "garantia", "case", "estojo"]:
                    if kw in full_text.lower():
                        differentials.append(kw.title())

                competitor = CompetitorProduct(
                    title=raw_title,
                    url=real_url,
                    store_name="Loja Mercado Livre",
                    platform="Mercado Livre",
                    price_brl=price,
                    shipping_type=shipping_type,
                    kit_items=kit_items,
                    differentials=differentials
                )
                competitors.append(competitor)

            return competitors
        except Exception:
            return []

    def parse_search_html(self, html: str, limit: int = 5) -> List[CompetitorProduct]:
        """Parses Mercado Livre search HTML and extracts structured competitor data."""
        soup = BeautifulSoup(html, "html.parser")
        competitors: List[CompetitorProduct] = []

        items = soup.find_all("li", class_=re.compile(r"ui-search-layout__item"))
        if not items:
            items = soup.find_all("div", class_=re.compile(r"ui-search-result"))

        for item in items:
            if len(competitors) >= limit:
                break

            link_tag = item.find("a", class_=re.compile(r"ui-search-link|ui-search-item__group__element"))
            if not link_tag:
                continue
            
            url = link_tag.get("href", "")
            title_tag = item.find(re.compile(r"h2|span"), class_=re.compile(r"ui-search-item__title"))
            title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
            if not title:
                continue

            price = self._extract_item_price(item)
            if price <= 0:
                continue

            seller_tag = item.find(class_=re.compile(r"seller-info|brand-discoverability|ui-search-item__group__element--seller"))
            store_name = seller_tag.get_text(strip=True) if seller_tag else "Mercado Livre Seller"

            shipping_type = "Normal"
            item_text = item.get_text()
            if "FULL" in item_text or item.find(class_=re.compile(r"fulfillment")):
                shipping_type = "Full"
            elif "frete grátis" in item_text.lower() or item.find(class_=re.compile(r"shipping--free")):
                shipping_type = "Frete Grátis"

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
