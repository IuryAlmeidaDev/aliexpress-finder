import requests
from typing import Optional
from src.competitors.extractors.base import BaseExtractor
from src.competitors.extractors.mercadolivre import MercadoLivreExtractor
from src.competitors.extractors.universal import UniversalWebExtractor
from src.competitors.models import TargetProduct

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

EXTRACTORS = [
    MercadoLivreExtractor,
    UniversalWebExtractor,  # Always last as fallback
]

def get_extractor_for_url(url: str) -> BaseExtractor:
    """Returns the most specific extractor capable of handling the URL."""
    for extractor_cls in EXTRACTORS:
        ext = extractor_cls()
        if ext.can_handle(url):
            return ext
    return UniversalWebExtractor()

def fetch_product_from_url(url: str, timeout: int = 15) -> TargetProduct:
    """Fetches HTML from URL using stealth client when available and extracts product info."""
    html = ""
    if HAS_CURL_CFFI:
        try:
            resp = curl_requests.get(url, impersonate="chrome124", timeout=timeout)
            if resp.status_code == 200:
                html = resp.text
        except Exception:
            pass

    if not html:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text

    extractor = get_extractor_for_url(url)
    return extractor.extract(url, html)
