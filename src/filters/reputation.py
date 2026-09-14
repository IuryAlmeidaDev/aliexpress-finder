def satisfies_reputation(rating: float, sales: int, min_rating: float = 4.5, min_sales: int = 10) -> bool:
    if rating < min_rating:
        return False
    if sales < min_sales:
        return False
    return True
