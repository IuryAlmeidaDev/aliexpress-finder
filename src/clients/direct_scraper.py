import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from src.clients.base_client import BaseSearchClient

def parse_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)*)", price_str)
    if not m:
        return 0.0
    clean = m.group(1)
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0

def parse_sales(sales_str: str) -> int:
    if not sales_str:
        return 0
    m_k = re.search(r"(\d+(?:[.,]\d+)?)\s*([kKmM])", sales_str)
    if m_k:
        val = float(m_k.group(1).replace(",", "."))
        mult = 1_000 if m_k.group(2).lower() == "k" else 1_000_000
        return int(val * mult)
    clean = re.sub(r"[^\d.,]", "", sales_str)
    if not clean:
        return 0
    if re.match(r"^\d{1,3}(?:[.,]\d{3})+$", clean):
        clean = re.sub(r"[.,]", "", clean)
        return int(clean)
    m = re.search(r"\d+", clean)
    return int(m.group(0)) if m else 0

def parse_aliexpress_html_items(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    cards = soup.find_all("div", class_=lambda c: c and "search-item-card" in c)
    if not cards:
        cards = soup.find_all("div", class_=lambda c: c and ("list--gallery--" in c or "multi--content--" in c))

    for card in cards:
        product_id = card.get("data-product-id") or ""
        link_el = card.find("a", href=True)
        url = link_el["href"] if link_el else ""
        if url.startswith("//"):
            url = "https:" + url

        if not product_id and url:
            m = re.search(r"/item/(\d+)\.html", url)
            if m:
                product_id = m.group(1)

        title_el = card.find(class_=lambda c: c and ("title" in c.lower()))
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = card.find(class_=lambda c: c and ("price" in c.lower()))
        price = 0.0
        if price_el:
            aria_label = price_el.get("aria-label")
            if aria_label:
                price = parse_price(aria_label)
            if price == 0.0:
                sale_el = card.find(class_=lambda c: c and ("price-sale" in c.lower() or "sale-price" in c.lower()))
                if sale_el:
                    price = parse_price(sale_el.get_text(strip=True))
                else:
                    price = parse_price(price_el.get_text(strip=True))

        trade_el = card.find(class_=lambda c: c and ("trade" in c.lower() or "sold" in c.lower()))
        sales = parse_sales(trade_el.get_text(strip=True)) if trade_el else 0

        eval_el = card.find(class_=lambda c: c and ("evaluation" in c.lower() or "rating" in c.lower() or "star" in c.lower()))
        try:
            rating = float(re.search(r"\d+\.\d+", eval_el.get_text(strip=True)).group(0)) if eval_el else 0.0
        except (AttributeError, ValueError):
            rating = 0.0

        if title and price > 0:
            items.append({
                "id": product_id,
                "title": title,
                "price": price,
                "shipping": 0.0,
                "sales": sales,
                "rating": rating,
                "url": url,
            })

    return items

class DirectAliExpressClient(BaseSearchClient):
    SEARCH_URL = "https://pt.aliexpress.com/w/wholesale-{query}.html"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        try:
            from curl_cffi import requests as curl_requests
            self.session = curl_requests.Session(impersonate="chrome124")
        except Exception:
            self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        self.session.cookies.set("aep_usuc_f", "site=bra&c_tp=BRL&region=BR&b_locale=pt_BR", domain=".aliexpress.com")

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        import time
        clean_query = query.replace(" ", "-")
        url = self.SEARCH_URL.format(query=urllib.parse.quote(clean_query))
        items: List[Dict[str, Any]] = []
        page = 1
        max_pages = max(1, (max_items + 11) // 12)

        while len(items) < max_items and page <= max_pages:
            params = {
                "SortType": "price_asc",
                "g": "y",
                "page": page,
            }
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                if "punish" in response.text or "x5sec" in response.text:
                    break
                page_items = parse_aliexpress_html_items(response.text)
                if not page_items:
                    break
                seen = {it.get("id") or it.get("url") for it in items}
                for it in page_items:
                    key = it.get("id") or it.get("url")
                    if key and key not in seen:
                        seen.add(key)
                        items.append(it)
                    elif not key:
                        items.append(it)
                page += 1
                if page <= max_pages and len(items) < max_items:
                    time.sleep(1.0)
            except Exception:
                break

        return items[:max_items]
