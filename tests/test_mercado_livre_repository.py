from datetime import datetime, timedelta, timezone

from src.mercado_livre.models import RadarProduct
from src.mercado_livre.repository import RadarRepository


def test_finds_only_comparable_weekly_observation(tmp_path):
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    product = RadarProduct("MLB1", "ITEM", "MLB10", "Produto", rank=3, review_count=15)
    with RadarRepository(str(tmp_path / "radar.db")) as repo:
        repo.start_run("old", "weekly", {}, now - timedelta(days=7))
        old = RadarProduct("MLB1", "ITEM", "MLB10", "Produto", rank=7, review_count=10)
        repo.save_observation("old", old, now - timedelta(days=7))
        previous = repo.previous_observation(product, now)
    assert previous["rank"] == 7
    assert previous["review_count"] == 10


def test_category_selection_reserves_space_for_unseen_categories(tmp_path):
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    with RadarRepository(str(tmp_path / "radar.db")) as repo:
        repo.mark_categories_visited([f"OLD{i}" for i in range(10)], now)
        chosen = repo.choose_categories(
            [f"OLD{i}" for i in range(10)] + ["NEW1", "NEW2"], limit=10
        )
    assert len(chosen) == 10
    assert {"NEW1", "NEW2"}.issubset(chosen)
