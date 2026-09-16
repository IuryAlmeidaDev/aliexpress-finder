import requests
from typing import Optional
from src.competitors.extractors.base import BaseExtractor
from src.competitors.extractors.mercadolivre import MercadoLivreExtractor
from src.competitors.extractors.universal import UniversalWebExtractor
from src.competitors.models import TargetProduct

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
    """Fetches HTML from URL and extracts target product information."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    extractor = get_extractor_for_url(url)
    return extractor.extract(url, response.text)
