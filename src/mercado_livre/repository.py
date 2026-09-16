from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from .models import RadarProduct, RadarScore


class RadarRepository:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                errors_json TEXT NOT NULL DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(id),
                entity_key TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                category_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                rank INTEGER,
                review_count INTEGER,
                review_average REAL,
                raw_json TEXT NOT NULL,
                UNIQUE(run_id, entity_key)
            );
            CREATE INDEX IF NOT EXISTS idx_observation_history
                ON observations(entity_key, category_id, observed_at);
            CREATE TABLE IF NOT EXISTS scores (
                run_id TEXT NOT NULL REFERENCES runs(id),
                entity_key TEXT NOT NULL,
                demand_score REAL NOT NULL,
                demand_coverage REAL NOT NULL,
                brand_score REAL NOT NULL,
                brand_coverage REAL NOT NULL,
                combined_score REAL NOT NULL,
                priority INTEGER NOT NULL,
                details_json TEXT NOT NULL,
                PRIMARY KEY(run_id, entity_key)
            );
            CREATE TABLE IF NOT EXISTS category_visits (
                category_id TEXT PRIMARY KEY,
                last_visited_at TEXT NOT NULL,
                visit_count INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        self.connection.commit()

    def start_run(self, run_id: str, mode: str, config: dict[str, Any], started_at: datetime) -> None:
        cutoff = (started_at - timedelta(hours=12)).isoformat()
        active = self.connection.execute(
            "SELECT id FROM runs WHERE status='running' AND started_at>=? LIMIT 1", (cutoff,)
        ).fetchone()
        if active:
            raise RuntimeError(f"Já existe uma execução ativa do radar: {active['id']}")
        self.connection.execute(
            "INSERT INTO runs(id, started_at, mode, status, config_json) VALUES (?, ?, ?, ?, ?)",
            (run_id, started_at.isoformat(), mode, "running", json.dumps(config, ensure_ascii=False)),
        )
        self.connection.commit()

    def choose_categories(self, candidates: list[str], limit: int) -> list[str]:
        if not candidates:
            return []
        rows = self.connection.execute(
            "SELECT category_id, last_visited_at, visit_count FROM category_visits"
        ).fetchall()
        history = {str(row["category_id"]): dict(row) for row in rows}
        established = [category for category in candidates if category in history]
        unseen = [category for category in candidates if category not in history]
        established.sort(
            key=lambda category: (
                int(history[category]["visit_count"]), history[category]["last_visited_at"]
            ),
            reverse=True,
        )
        rotation_size = max(1, round(limit * 0.20))
        chosen = established[: max(0, limit - rotation_size)]
        exploration = unseen + sorted(
            (category for category in established if category not in chosen),
            key=lambda category: history[category]["last_visited_at"],
        )
        chosen.extend(exploration[: max(0, limit - len(chosen))])
        for category in candidates:
            if len(chosen) >= limit:
                break
            if category not in chosen:
                chosen.append(category)
        return chosen

    def mark_categories_visited(self, category_ids: list[str], visited_at: datetime) -> None:
        for category_id in category_ids:
            self.connection.execute(
                """
                INSERT INTO category_visits(category_id, last_visited_at, visit_count)
                VALUES (?, ?, 1)
                ON CONFLICT(category_id) DO UPDATE SET
                    last_visited_at=excluded.last_visited_at,
                    visit_count=category_visits.visit_count + 1
                """,
                (category_id, visited_at.isoformat()),
            )
        self.connection.commit()

    def finish_run(self, run_id: str, status: str, errors: list[str], finished_at: datetime) -> None:
        self.connection.execute(
            "UPDATE runs SET finished_at=?, status=?, errors_json=? WHERE id=?",
            (finished_at.isoformat(), status, json.dumps(errors, ensure_ascii=False), run_id),
        )
        self.connection.commit()

    def save_observation(self, run_id: str, product: RadarProduct, observed_at: datetime) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO observations(
                run_id, entity_key, entity_id, entity_type, category_id, observed_at,
                title, url, rank, review_count, review_average, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, product.entity_key, product.entity_id, product.entity_type,
                product.category_id, observed_at.isoformat(), product.title, product.url,
                product.rank, product.review_count, product.review_average,
                json.dumps(product.raw, ensure_ascii=False),
            ),
        )
        self.connection.commit()

    def previous_observation(
        self, product: RadarProduct, observed_at: datetime
    ) -> Optional[dict[str, Any]]:
        upper = (observed_at - timedelta(days=5)).isoformat()
        lower = (observed_at - timedelta(days=9)).isoformat()
        row = self.connection.execute(
            """
            SELECT rank, review_count, review_average, observed_at
            FROM observations
            WHERE entity_key=? AND category_id=? AND observed_at BETWEEN ? AND ?
            ORDER BY ABS(julianday(observed_at) - julianday(?)) ASC LIMIT 1
            """,
            (product.entity_key, product.category_id, lower, upper, (observed_at - timedelta(days=7)).isoformat()),
        ).fetchone()
        return dict(row) if row else None

    def save_score(self, run_id: str, product: RadarProduct, score: RadarScore) -> None:
        details = {
            "demand_reasons": score.demand_reasons,
            "brand_reasons": score.brand_reasons,
            "counterpoints": score.counterpoints,
        }
        self.connection.execute(
            """
            INSERT OR REPLACE INTO scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, product.entity_key, score.demand_score, score.demand_coverage,
                score.brand_score, score.brand_coverage, score.combined_score,
                int(score.priority), json.dumps(details, ensure_ascii=False),
            ),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "RadarRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
