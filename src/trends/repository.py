"""SQLite repository for Trend Radar data."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .models import TrendTerm
from .terms import get_default_terms


class TrendRepository:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.row_factory = sqlite3.Row

    def close(self):
        self._conn.close()

    def initialize(self):
        c = self._conn
        c.executescript("""
            CREATE TABLE IF NOT EXISTS trend_terms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                term        TEXT NOT NULL UNIQUE,
                category    TEXT NOT NULL,
                source      TEXT NOT NULL DEFAULT 'both',
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL,
                last_hit_at TEXT
            );
            CREATE TABLE IF NOT EXISTS trend_snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                term_id         INTEGER NOT NULL REFERENCES trend_terms(id),
                source          TEXT NOT NULL,
                product_id      TEXT NOT NULL,
                title           TEXT NOT NULL,
                price_brl       REAL,
                price_usd       REAL,
                sales_total     INTEGER,
                rating          REAL,
                moq             INTEGER,
                supplier_name   TEXT,
                is_verified     INTEGER,
                url             TEXT NOT NULL,
                collected_at    TEXT NOT NULL,
                UNIQUE(source, product_id, collected_at)
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_product
                ON trend_snapshots(source, product_id, collected_at);
            CREATE INDEX IF NOT EXISTS idx_snapshots_term
                ON trend_snapshots(term_id, collected_at);
            CREATE INDEX IF NOT EXISTS idx_snapshots_collected_at
                ON trend_snapshots(collected_at);
            CREATE TABLE IF NOT EXISTS trend_opportunities (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id         INTEGER NOT NULL REFERENCES trend_snapshots(id),
                product_id          TEXT NOT NULL,
                source              TEXT NOT NULL,
                sales_velocity_7d   INTEGER,
                sales_velocity_30d  INTEGER,
                acceleration        REAL,
                ml_query            TEXT,
                ml_competitors      INTEGER,
                ml_avg_price        REAL,
                ml_min_price        REAL,
                ml_full_share_pct   REAL,
                ml_total_sales_br   INTEGER,
                landed_cost_brl     REAL,
                suggested_price_brl REAL,
                net_margin_pct      REAL,
                strategy            TEXT NOT NULL,
                trend_score         REAL NOT NULL,
                calculated_at       TEXT NOT NULL,
                UNIQUE(product_id, source, calculated_at)
            );
            CREATE INDEX IF NOT EXISTS idx_opportunities_strategy
                ON trend_opportunities(strategy, trend_score DESC);
        """)

    def seed_default_terms(self):
        now = datetime.now(timezone.utc).isoformat()
        for t in get_default_terms():
            self._conn.execute(
                "INSERT OR IGNORE INTO trend_terms (term, category, source, active, created_at) "
                "VALUES (?, ?, ?, 1, ?)",
                (t["term"], t["category"], t["source"], now)
            )
        self._conn.commit()

    def get_active_terms(self) -> list[TrendTerm]:
        rows = self._conn.execute(
            "SELECT id, term, category, source, active, created_at, last_hit_at "
            "FROM trend_terms WHERE active = 1 ORDER BY id"
        ).fetchall()
        return [TrendTerm(id=r["id"], term=r["term"], category=r["category"],
                          source=r["source"], active=bool(r["active"]),
                          created_at=r["created_at"], last_hit_at=r["last_hit_at"])
                for r in rows]

    def save_snapshots(self, snapshots: list[dict]):
        for s in snapshots:
            self._conn.execute(
                "INSERT OR IGNORE INTO trend_snapshots "
                "(term_id, source, product_id, title, price_brl, price_usd, "
                "sales_total, rating, moq, supplier_name, is_verified, url, collected_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (s["term_id"], s["source"], s["product_id"], s["title"],
                 s.get("price_brl"), s.get("price_usd"), s.get("sales_total"),
                 s.get("rating"), s.get("moq"), s.get("supplier_name"),
                 s.get("is_verified"), s["url"], s["collected_at"])
            )
        self._conn.commit()

    def get_latest_snapshot(self, product_id: str, source: str) -> dict | None:
        row = self._conn.execute(
            "SELECT title, url, price_brl, sales_total, rating, moq, "
            "supplier_name, is_verified FROM trend_snapshots "
            "WHERE product_id = ? AND source = ? ORDER BY collected_at DESC LIMIT 1",
            (product_id, source)
        ).fetchone()
        return dict(row) if row else None

    def get_latest_snapshot_id(self, product_id: str, source: str) -> int | None:
        row = self._conn.execute(
            "SELECT id FROM trend_snapshots WHERE product_id = ? AND source = ? "
            "ORDER BY collected_at DESC LIMIT 1",
            (product_id, source)
        ).fetchone()
        return row["id"] if row else None

    def get_snapshots_for_velocity(self, product_id: str, source: str,
                                   days: int) -> list[tuple[str, int]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self._conn.execute(
            "SELECT collected_at, sales_total FROM trend_snapshots "
            "WHERE product_id = ? AND source = ? AND collected_at >= ? "
            "AND sales_total IS NOT NULL "
            "ORDER BY collected_at ASC",
            (product_id, source, cutoff)
        ).fetchall()
        return [(r["collected_at"], r["sales_total"]) for r in rows]

    def get_all_product_ids_with_snapshots(self, min_days: int = 2) -> list[tuple[str, str, str]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=min_days)).strftime("%Y-%m-%d")
        rows = self._conn.execute(
            "SELECT DISTINCT s.product_id, s.source, t.category "
            "FROM trend_snapshots s JOIN trend_terms t ON s.term_id = t.id "
            "WHERE s.sales_total IS NOT NULL "
            "GROUP BY s.product_id, s.source, t.category "
            "HAVING MIN(s.collected_at) <= ? AND COUNT(*) >= 2",
            (cutoff,)
        ).fetchall()
        return [(r["product_id"], r["source"], r["category"]) for r in rows]

    def save_opportunities(self, opportunities: list[dict]):
        for o in opportunities:
            self._conn.execute(
                "INSERT OR REPLACE INTO trend_opportunities "
                "(snapshot_id, product_id, source, sales_velocity_7d, sales_velocity_30d, "
                "acceleration, ml_query, ml_competitors, ml_avg_price, ml_min_price, "
                "ml_full_share_pct, ml_total_sales_br, landed_cost_brl, "
                "suggested_price_brl, net_margin_pct, strategy, trend_score, calculated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (o["snapshot_id"], o["product_id"], o["source"],
                 o.get("sales_velocity_7d"), o.get("sales_velocity_30d"),
                 o.get("acceleration"), o.get("ml_query"),
                 o.get("ml_competitors"), o.get("ml_avg_price"), o.get("ml_min_price"),
                 o.get("ml_full_share_pct"), o.get("ml_total_sales_br"),
                 o.get("landed_cost_brl"), o.get("suggested_price_brl"),
                 o.get("net_margin_pct"), o["strategy"], o["trend_score"],
                 o["calculated_at"])
            )
        self._conn.commit()

    def get_trending(self, strategy: Optional[str] = None,
                     category: Optional[str] = None, limit: int = 100) -> list[dict]:
        query = (
            "SELECT o.*, s.title, s.url, s.price_brl, s.sales_total, "
            "s.rating, s.moq, s.supplier_name, s.is_verified, t.category "
            "FROM trend_opportunities o "
            "JOIN trend_snapshots s ON o.snapshot_id = s.id "
            "JOIN trend_terms t ON s.term_id = t.id "
            "WHERE 1=1 "
        )
        params: list = []
        if strategy:
            query += "AND o.strategy = ? "
            params.append(strategy)
        if category:
            query += "AND t.category = ? "
            params.append(category)
        query += "ORDER BY o.trend_score DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_product_history(self, product_id: str, source: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT collected_at, sales_total, price_brl "
            "FROM trend_snapshots "
            "WHERE product_id = ? AND source = ? "
            "ORDER BY collected_at ASC",
            (product_id, source)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_sparkline(self, product_id: str, source: str, points: int = 30) -> list[int]:
        rows = self._conn.execute(
            "SELECT sales_total FROM trend_snapshots "
            "WHERE product_id = ? AND source = ? AND sales_total IS NOT NULL "
            "ORDER BY collected_at ASC",
            (product_id, source)
        ).fetchall()
        values = [r["sales_total"] for r in rows]
        return values[-points:] if len(values) > points else values

    def get_stats(self) -> dict:
        total = self._conn.execute(
            "SELECT COUNT(DISTINCT product_id || '|' || source) as c FROM trend_snapshots"
        ).fetchone()["c"]
        strategies = self._conn.execute(
            "SELECT strategy, COUNT(*) as c FROM trend_opportunities "
            "GROUP BY strategy"
        ).fetchall()
        strat_counts = {r["strategy"]: r["c"] for r in strategies}
        top_row = self._conn.execute(
            "SELECT s.title, o.sales_velocity_7d FROM trend_opportunities o "
            "JOIN trend_snapshots s ON o.snapshot_id = s.id "
            "ORDER BY o.sales_velocity_7d DESC LIMIT 1"
        ).fetchone()
        top_accel = (
            {"title": top_row["title"], "velocity_7d": top_row["sales_velocity_7d"]}
            if top_row else {"title": "", "velocity_7d": 0}
        )
        by_cat = self._conn.execute(
            "SELECT t.category, COUNT(*) as c FROM trend_opportunities o "
            "JOIN trend_snapshots s ON o.snapshot_id = s.id "
            "JOIN trend_terms t ON s.term_id = t.id "
            "GROUP BY t.category ORDER BY c DESC"
        ).fetchall()
        return {
            "total_monitored": total,
            "ocean_blue_count": strat_counts.get("OCEANO_AZUL", 0),
            "trending_count": strat_counts.get("TENDENCIA", 0),
            "emerging_count": strat_counts.get("EMERGENTE", 0),
            "top_acceleration": top_accel,
            "by_category": [{"category": r["category"], "count": r["c"]} for r in by_cat],
        }

    def cleanup_old(self, days: int = 90):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        self._conn.execute(
            "DELETE FROM trend_opportunities WHERE snapshot_id IN "
            "(SELECT id FROM trend_snapshots WHERE collected_at < ?)", (cutoff,)
        )
        self._conn.execute("DELETE FROM trend_snapshots WHERE collected_at < ?", (cutoff,))
        self._conn.commit()

    def deactivate_stale_terms(self, inactive_days: int = 30):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=inactive_days)).strftime("%Y-%m-%d")
        self._conn.execute(
            "UPDATE trend_terms SET active = 0 "
            "WHERE active = 1 AND created_at < ? AND id NOT IN ("
            "  SELECT DISTINCT term_id FROM trend_snapshots WHERE collected_at >= ?"
            ")", (cutoff, cutoff)
        )
        self._conn.commit()
