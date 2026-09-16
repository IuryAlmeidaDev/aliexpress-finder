"""Extractors for various e-commerce platforms and generic web stores."""
from src.competitors.extractors.base import BaseExtractor
from src.competitors.extractors.mercadolivre import MercadoLivreExtractor
from src.competitors.extractors.universal import UniversalWebExtractor
from src.competitors.extractors.router import get_extractor_for_url

__all__ = [
    "BaseExtractor",
    "MercadoLivreExtractor",
    "UniversalWebExtractor",
    "get_extractor_for_url",
]
