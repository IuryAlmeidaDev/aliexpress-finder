from typing import List, Dict, Any
from src.filters.anti_trick import is_accessory_trick
from src.filters.semantic import matches_semantic_criteria
from src.filters.reputation import satisfies_reputation

class FilterPipeline:
    def __init__(self, min_rating: float = 4.5, min_sales: int = 10):
        self.min_rating = min_rating
        self.min_sales = min_sales

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
            rating = float(item.get("rating", 0.0))
            sales = int(item.get("sales", 0))

            if is_accessory_trick(title, search_query):
                continue

            if not matches_semantic_criteria(title, include_terms, exclude_terms):
                continue

            if not satisfies_reputation(rating, sales, self.min_rating, self.min_sales):
                continue

            passed.append(item)

        return passed
