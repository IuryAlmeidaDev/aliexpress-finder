import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.competitors.models import TargetProduct

NOISE_WORDS = [
    r"\boriginal\b",
    r"\bpronta entrega\b",
    r"\bfrete gr[aá]tis\b",
    r"\bpromo[cç][aã]o\b",
    r"\bcom nota fiscal\b",
    r"\bnota fiscal\b",
    r"\bnf\b",
    r"\benvio r[aá]pido\b",
    r"\bnovo\b",
    r"\bbarato\b",
    r"\blan[cç]amento\b",
    r"\btop\b",
    r"\bpremium\b",
    r"\b100%\b",
]

COMMON_KIT_KEYWORDS = [
    "estojo rígido",
    "estojo",
    "flanela de limpeza",
    "flanela",
    "case",
    "caixa",
    "pulseira extra",
    "ferramenta",
    "manual",
    "cabo usb",
    "cabo",
    "bateria",
    "pilha",
    "suporte",
    "certificado",
]

class BaseExtractor(ABC):
    """Abstract base class for product extractors."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Determines if this extractor can process the given URL."""
        pass

    @abstractmethod
    def extract(self, url: str, html: str) -> TargetProduct:
        """Extracts product information from HTML into a TargetProduct."""
        pass

    @staticmethod
    def clean_title(title: str) -> str:
        """Cleans marketing buzzwords to create a focused search query."""
        cleaned = title
        # Remove price suffix (e.g. ' - R$ 58,11')
        cleaned = re.sub(r"-\s*R\$\s*[\d\.,]+.*$", "", cleaned, flags=re.IGNORECASE)
        # Remove common noise words
        for pattern in NOISE_WORDS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        # Remove extra punctuation and multiple spaces
        cleaned = re.sub(r"[\|\–\—\-\/\+]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def detect_kit_items(text: str) -> List[str]:
        """Detects accessories and kit inclusions from product text."""
        detected = []
        lower_text = text.lower()
        for kw in COMMON_KIT_KEYWORDS:
            if kw in lower_text and kw not in detected:
                detected.append(kw)
        return detected
