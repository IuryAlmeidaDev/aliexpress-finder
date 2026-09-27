from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.trends.collector import collect_trends, BLOCK_SIZE
from src.trends.repository import TrendRepository


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    return repo


def _mock_ali_search(query, limit=20):
    return [
        {"id": f"ali_{query[:5]}_{i}", "title": f"Product {query} {i}",
         "price": 50.0 + i, "shipping": 0.0, "sales": 1000 + i * 100,
         "rating": 4.5, "url": f"https://aliexpress.com/item/ali_{query[:5]}_{i}.html"}
        for i in range(min(3, limit))
    ]


def _mock_alibaba_search(query, limit=20):
    return [
        {"id": f"baba_{query[:5]}_{i}", "title": f"Alibaba {query} {i}",
         "price": 30.0 + i, "moq": 100, "supplier_name": f"Factory {i}",
         "is_verified": True, "has_trade_assurance": True,
         "years_in_business": 5, "url": f"https://alibaba.com/product/baba_{query[:5]}_{i}.html"}
        for i in range(min(2, limit))
    ]


@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_collect_saves_snapshots(mock_ali_cls, mock_baba_cls):
    mock_ali = MagicMock()
    mock_ali.search.side_effect = _mock_ali_search
    mock_ali_cls.return_value = mock_ali

    mock_baba = MagicMock()
    mock_baba.search.side_effect = _mock_alibaba_search
    mock_baba_cls.return_value = mock_baba

    repo = _make_repo()
    result = collect_trends(repo, block_pause=0, request_delay=(0, 0))
    assert result["collected"] > 0
    assert result["blocked"] is False


@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_collect_handles_empty_results(mock_ali_cls, mock_baba_cls):
    mock_ali = MagicMock()
    mock_ali.search.return_value = []
    mock_ali_cls.return_value = mock_ali

    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba

    repo = _make_repo()
    result = collect_trends(repo, block_pause=0, request_delay=(0, 0))
    assert result["collected"] == 0
    assert result["skipped_terms"] == 0


@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_collect_handles_scraper_exception(mock_ali_cls, mock_baba_cls):
    mock_ali = MagicMock()
    mock_ali.search.side_effect = Exception("Captcha detected")
    mock_ali_cls.return_value = mock_ali

    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba

    repo = _make_repo()
    result = collect_trends(repo, block_pause=0, request_delay=(0, 0))
    assert result["skipped_terms"] > 0
    assert result["blocked"] is False  # individual failures don't set blocked


def test_block_size_constant():
    assert BLOCK_SIZE == 15
