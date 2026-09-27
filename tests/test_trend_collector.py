from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.trends.collector import collect_trends, BLOCK_SIZE
from src.trends.repository import TrendRepository


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    return repo


def _mock_ali_search(query, max_items=20, **kwargs):
    return [
        {"id": f"ali_{query[:5]}_{i}", "title": f"Product {query} {i}",
         "price": 50.0 + i, "shipping": 0.0, "sales": 1000 + i * 100,
         "rating": 4.5, "url": f"https://aliexpress.com/item/ali_{query[:5]}_{i}.html"}
        for i in range(min(3, max_items))
    ]


def _mock_alibaba_search(query, max_items=20, **kwargs):
    return [
        {"id": f"baba_{query[:5]}_{i}", "title": f"Alibaba {query} {i}",
         "price": 30.0 + i, "moq": 100, "supplier_name": f"Factory {i}",
         "is_verified": True, "has_trade_assurance": True,
         "years_in_business": 5, "url": f"https://alibaba.com/product/baba_{query[:5]}_{i}.html"}
        for i in range(min(2, max_items))
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

    # Verify baba_client received usd_rate
    assert mock_baba_cls.call_args.kwargs.get("usd_rate") is not None


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


def test_collect_empty_terms_returns_early():
    repo = TrendRepository(":memory:")
    repo.initialize()
    result = collect_trends(repo)
    assert result == {"collected": 0, "skipped_terms": 0, "blocked": False}


@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_collect_source_filtering(mock_ali_cls, mock_baba_cls):
    mock_ali = MagicMock()
    mock_ali.search.return_value = []
    mock_ali_cls.return_value = mock_ali

    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba

    repo = TrendRepository(":memory:")
    repo.initialize()
    now = datetime.now(timezone.utc).isoformat()
    repo._conn.execute(
        "INSERT INTO trend_terms (term, category, source, active, created_at) "
        "VALUES ('ali_only_term', 'electronics', 'ali', 1, ?)", (now,)
    )
    repo._conn.execute(
        "INSERT INTO trend_terms (term, category, source, active, created_at) "
        "VALUES ('baba_only_term', 'electronics', 'alibaba', 1, ?)", (now,)
    )
    repo._conn.commit()

    collect_trends(repo, block_pause=0, request_delay=(0, 0))

    mock_ali.search.assert_called_once_with("ali_only_term", max_items=20)
    mock_baba.search.assert_called_once_with("baba_only_term", max_items=20)


@patch("src.trends.collector.time.sleep")
@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_collect_multi_block_and_pauses(mock_ali_cls, mock_baba_cls, mock_sleep):
    mock_ali = MagicMock()
    mock_ali.search.return_value = []
    mock_ali_cls.return_value = mock_ali

    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba

    repo = TrendRepository(":memory:")
    repo.initialize()
    now = datetime.now(timezone.utc).isoformat()
    # Insert 16 active terms (BLOCK_SIZE + 1)
    for i in range(16):
        repo._conn.execute(
            "INSERT INTO trend_terms (term, category, source, active, created_at) "
            "VALUES (?, 'category', 'ali', 1, ?)", (f"term_{i}", now)
        )
    repo._conn.commit()

    collect_trends(repo, block_pause=10.0, request_delay=(0, 0))

    # Expect exactly one block pause between block 1 and block 2 (none after block 2)
    mock_sleep.assert_called_once_with(10.0)


def test_block_size_constant():
    assert BLOCK_SIZE == 15
