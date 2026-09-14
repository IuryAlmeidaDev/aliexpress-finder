import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from src.clients.base_client import BaseSearchClient

def parse_moq(moq_str: str) -> int:
    if not moq_str:
        return 1
    m = re.search(r"(\d+[\d\s,]*)", moq_str)
    if not m:
        return 1
    clean = re.sub(r"[^\d]", "", m.group(1))
    try:
        val = int(clean)
        return val if val > 0 else 1
    except ValueError:
        return 1

def parse_alibaba_price(price_str: str, usd_rate: float = 5.50) -> float:
    if not price_str:
        return 0.0
    clean = price_str.strip()
    is_usd = "$" in clean or "USD" in clean.upper() or "US" in clean.upper()
    if "R$" in clean:
        is_usd = False

    # Extract first price token
    m = re.search(r"(\d+(?:[.,]\d+)?)", clean)
    if not m:
        return 0.0
    num_str = m.group(1)
    if "," in num_str and "." in num_str:
        num_str = num_str.replace(".", "").replace(",", ".")
    elif "," in num_str:
        num_str = num_str.replace(",", ".")
    try:
        val = float(num_str)
        if is_usd:
            return round(val * usd_rate, 2)
        return round(val, 2)
    except ValueError:
        return 0.0

def parse_alibaba_html_items(html: str, usd_rate: float = 5.50) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    cards = soup.find_all("div", class_=lambda c: c and ("organic-list-offer" in c or "search-card-e" in c or "fy23-gallery-card" in c or "list-no-v2-outer" in c))
    if not cards:
        cards = soup.find_all("div", attrs={"data-spm": lambda s: s and "offer" in s})

    for card in cards:
        link_el = card.find("a", href=True)
        url = link_el["href"] if link_el else ""
        if url.startswith("//"):
            url = "https:" + url

        product_id = ""
        m_id = re.search(r"_(\d+)\.html", url)
        if m_id:
            product_id = m_id.group(1)

        title_el = card.find(class_=lambda c: c and ("title" in c.lower()))
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = card.find(class_=lambda c: c and ("price" in c.lower()))
        price = parse_alibaba_price(price_el.get_text(strip=True), usd_rate=usd_rate) if price_el else 0.0

        moq_el = card.find(class_=lambda c: c and ("minorder" in c.lower() or "moq" in c.lower() or "min-order" in c.lower()))
        moq = parse_moq(moq_el.get_text(strip=True)) if moq_el else 1

        company_el = card.find(class_=lambda c: c and ("company" in c.lower() or "supplier" in c.lower() or "seller" in c.lower()))
        supplier_name = company_el.get_text(strip=True) if company_el else ""

        card_text = card.get_text()
        is_verified = "verified" in card_text.lower()
        has_trade_assurance = "trade assurance" in card_text.lower()

        years = 0
        m_yrs = re.search(r"(\d+)\s*(?:yrs|anos|years)", card_text, re.IGNORECASE)
        if m_yrs:
            try:
                years = int(m_yrs.group(1))
            except ValueError:
                years = 0

        if title and price > 0:
            items.append({
                "id": product_id,
                "title": title,
                "price": price,
                "moq": moq,
                "supplier_name": supplier_name,
                "is_verified": is_verified,
                "has_trade_assurance": has_trade_assurance,
                "years_in_business": years,
                "url": url,
            })

    return items

class DirectAlibabaClient(BaseSearchClient):
    SEARCH_URL = "https://www.alibaba.com/trade/search?SearchText={query}"

    def __init__(self, timeout: int = 15, usd_rate: float = 5.50):
        self.timeout = timeout
        self.usd_rate = usd_rate
        try:
            from curl_cffi import requests as curl_requests
            self.session = curl_requests.Session(impersonate="chrome124")
        except Exception:
            self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        import time
        url = self.SEARCH_URL.format(query=urllib.parse.quote(query))
        items: List[Dict[str, Any]] = []
        page = 1
        max_pages = max(1, (max_items + 11) // 12)

        while len(items) < max_items and page <= max_pages:
            params = {"page": page}
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                page_items = parse_alibaba_html_items(response.text, usd_rate=self.usd_rate)
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
