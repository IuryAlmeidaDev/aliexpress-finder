from src.filters.alibaba_pipeline import AlibabaFilterPipeline

ITEMS = [
    {"title": "Kids Watch Silicone", "moq": 20, "is_verified": True, "has_trade_assurance": True},
    {"title": "Kids Watch LED", "moq": 100, "is_verified": True, "has_trade_assurance": False},
    {"title": "Kids Watch Quartz", "moq": 30, "is_verified": False, "has_trade_assurance": True},
    {"title": "Unrelated Toy", "moq": 10, "is_verified": True, "has_trade_assurance": True},
]

def test_filter_by_max_moq():
    pipeline = AlibabaFilterPipeline(max_moq=50)
    passed = pipeline.filter_products(ITEMS, search_query="watch")
    assert all(it["moq"] <= 50 for it in passed)
    assert len(passed) == 3

def test_filter_by_verified():
    pipeline = AlibabaFilterPipeline(only_verified=True)
    passed = pipeline.filter_products(ITEMS, search_query="watch")
    assert all(it["is_verified"] is True for it in passed)
    assert len(passed) == 3

def test_filter_by_trade_assurance():
    pipeline = AlibabaFilterPipeline(only_trade_assurance=True)
    passed = pipeline.filter_products(ITEMS, search_query="watch")
    assert all(it["has_trade_assurance"] is True for it in passed)
    assert len(passed) == 3

def test_filter_combined_moq_and_badges_and_semantics():
    pipeline = AlibabaFilterPipeline(max_moq=50, only_verified=True, only_trade_assurance=True)
    passed = pipeline.filter_products(
        ITEMS,
        search_query="watch",
        include_terms=["silicone"],
        exclude_terms=["quartz"]
    )
    assert len(passed) == 1
    assert passed[0]["title"] == "Kids Watch Silicone"
