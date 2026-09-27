"""Stage 2: Calculate sales velocity and acceleration from snapshots."""
from __future__ import annotations

from .models import TrendVelocity
from .repository import TrendRepository

MIN_TREND_VELOCITY = 100  # minimum Δ sales/7d to qualify


def calculate_velocity(repo: TrendRepository) -> list[TrendVelocity]:
    """Compute velocity for all eligible products, filter and sort."""
    products = repo.get_all_product_ids_with_snapshots(min_days=2)
    results: list[TrendVelocity] = []

    for product_id, source, category in products:
        snapshots_30d = repo.get_snapshots_for_velocity(product_id, source, days=30)
        if len(snapshots_30d) < 2:
            continue

        latest_date, latest_sales = snapshots_30d[-1]
        earliest_date, earliest_sales = snapshots_30d[0]

        # Find closest snapshot to 7 days ago
        snapshots_7d = repo.get_snapshots_for_velocity(product_id, source, days=7)
        if snapshots_7d and len(snapshots_7d) >= 2:
            sales_7d_ago = snapshots_7d[0][1]
            velocity_7d = latest_sales - sales_7d_ago
        elif len(snapshots_30d) >= 2:
            sales_7d_ago = snapshots_30d[0][1]
            velocity_7d = latest_sales - sales_7d_ago
        else:
            continue

        velocity_30d = latest_sales - earliest_sales

        # Filter negative velocity (data glitches)
        if velocity_7d < MIN_TREND_VELOCITY:
            continue

        # Acceleration: compare current week velocity vs previous week
        acceleration = 0.0
        snapshots_14d = repo.get_snapshots_for_velocity(product_id, source, days=14)
        if len(snapshots_14d) >= 3:
            # Find snapshot closest to 14 days ago and 7 days ago
            s14 = snapshots_14d[0][1]  # oldest in 14d window
            if snapshots_7d:
                s7 = snapshots_7d[0][1]
                prev_velocity = s7 - s14
                if prev_velocity > 0:
                    acceleration = ((velocity_7d - prev_velocity) / prev_velocity) * 100.0

        # Get latest snapshot details for title, url, price, etc.
        latest_row = repo.get_latest_snapshot(product_id, source)
        if not latest_row:
            continue

        results.append(TrendVelocity(
            product_id=product_id,
            source=source,
            title=latest_row["title"],
            url=latest_row["url"],
            category=category,
            price_brl=latest_row["price_brl"],
            sales_total=latest_row["sales_total"],
            sales_velocity_7d=velocity_7d,
            sales_velocity_30d=velocity_30d,
            acceleration=round(acceleration, 1),
            rating=latest_row["rating"],
            moq=latest_row["moq"],
            supplier_name=latest_row["supplier_name"],
            is_verified=bool(latest_row["is_verified"]) if latest_row["is_verified"] is not None else None,
        ))

    results.sort(key=lambda v: v.sales_velocity_7d, reverse=True)
    return results
