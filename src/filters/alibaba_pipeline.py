from typing import List, Dict, Any, Optional
from src.filters.semantic import matches_semantic_criteria

class AlibabaFilterPipeline:
    def __init__(
        self,
        max_moq: Optional[int] = None,
        only_verified: bool = False,
        only_trade_assurance: bool = False
    ):
        self.max_moq = max_moq
        self.only_verified = only_verified
        self.only_trade_assurance = only_trade_assurance

    def filter_products(
        self,
        items: List[Dict[str, Any]],
        search_query: str,
        include_terms: List[str] = None,
        exclude_terms: List[str] = None
    ) -> List[Dict[str, Any]]:
        include_terms = include_terms or []
        exclude_terms = exclude_terms or []
        passed = []

        for item in items:
            title = item.get("title", "")
            moq = int(item.get("moq") or 1)
            is_verified = bool(item.get("is_verified"))
            has_trade_assurance = bool(item.get("has_trade_assurance"))

            if self.max_moq is not None and moq > self.max_moq:
                continue

            if self.only_verified and not is_verified:
                continue

            if self.only_trade_assurance and not has_trade_assurance:
                continue

            if not matches_semantic_criteria(title, include_terms, exclude_terms):
                continue

            passed.append(item)

        return passed
