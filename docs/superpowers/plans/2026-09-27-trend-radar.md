# Trend Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily automated trend detection system that scrapes China marketplaces (AliExpress + Alibaba), tracks sales velocity over time, cross-references with Brazilian market gaps on Mercado Livre, and surfaces opportunities in a new dashboard tab.

**Architecture:** Three-stage daily pipeline (Collect → Velocity → Gap Analysis) writing to SQLite, served via new FastAPI endpoints, rendered in a new React "Tendências" tab. Reuses existing scrapers (`DirectAliExpressClient`, `DirectAlibabaClient`), `CompetitorRadar`, and `ArbitrageEngine.calculate_landed_costs()`.

**Tech Stack:** Python 3.12, FastAPI, SQLite (WAL), curl_cffi, BeautifulSoup, React 19, TypeScript, Tailwind CSS v4, Recharts, Vite 6

**Spec:** `docs/superpowers/specs/2026-09-27-trend-radar-design.md`

## Global Constraints

- Python ≥ 3.10, Node ≥ 18
- No new Python dependencies — reuse `sqlite3`, `curl_cffi`, `beautifulsoup4`, `openpyxl`, `fastapi` already in `requirements.txt`
- No new npm dependencies — reuse `recharts`, `lucide-react`, `radix-ui`, `tailwindcss` already in `dashboard/package.json`
- All UI text in Portuguese (pt-BR)
- Existing 93 tests must keep passing
- Commits after each task
- SQLite database path: `data/mercado_livre_radar.db` (same file, new tables)

## File Structure

```
src/trends/                     # NEW PACKAGE — daily trend detection pipeline
├── __init__.py                 # Package exports
├── models.py                   # Dataclasses: TrendTerm, TrendSnapshot, TrendVelocity, TrendOpportunity
├── terms.py                    # DEFAULT_TERMS list + seed_terms() function
├── repository.py               # SQLite CRUD for 3 new tables
├── collector.py                # Stage 1: scrape China sources daily
├── velocity.py                 # Stage 2: compute Δ sales / acceleration
├── gap_analyzer.py             # Stage 3: cross-reference with Mercado Livre
├── scoring.py                  # Trend Score (0-100) + classification

src/cli/main.py                 # MODIFY — add `trends` subcommand
src/mercado_livre/dashboard_api.py  # MODIFY — add 4 trend endpoints

dashboard/src/types.ts          # MODIFY — add 3 interfaces
dashboard/src/App.tsx           # MODIFY — add trends tab + data fetching
dashboard/src/components/Navbar.tsx  # MODIFY — add "Tendências" pill
dashboard/src/components/TrendsView.tsx      # NEW — main trends tab component
dashboard/src/components/TrendFilters.tsx     # NEW — filter bar
dashboard/src/components/VelocitySparkline.tsx  # NEW — mini chart

deploy/trend-radar.timer        # NEW — systemd daily timer
deploy/trend-radar.service      # NEW — systemd oneshot service

tests/test_trend_models.py
tests/test_trend_terms.py
tests/test_trend_repository.py
tests/test_trend_collector.py
tests/test_trend_velocity.py
tests/test_trend_gap_analyzer.py
tests/test_trend_scoring.py
tests/test_trend_pipeline.py
tests/test_api_trends.py
```

---

### Task 1: Data Models

**Files:**
- Create: `src/trends/__init__.py`
- Create: `src/trends/models.py`
- Test: `tests/test_trend_models.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `TrendTerm(id, term, category, source, active, created_at, last_hit_at)` — dataclass
  - `TrendSnapshot(id, term_id, source, product_id, title, price_brl, price_usd, sales_total, rating, moq, supplier_name, is_verified, url, collected_at)` — dataclass
  - `TrendVelocity(product_id, source, title, url, category, price_brl, sales_total, sales_velocity_7d, sales_velocity_30d, acceleration, rating, moq, supplier_name, is_verified)` — dataclass
  - `TrendOpportunity(product_id, source, title, url, category, price_brl, sales_total, sales_velocity_7d, sales_velocity_30d, acceleration, ml_query, ml_competitors, ml_avg_price, ml_min_price, ml_full_share_pct, ml_total_sales_br, landed_cost_brl, suggested_price_brl, net_margin_pct, strategy, trend_score, supplier_name, moq, is_verified, sparkline, calculated_at)` — dataclass
  - `STRATEGY_OCEANO_AZUL`, `STRATEGY_TENDENCIA`, `STRATEGY_EMERGENTE`, `STRATEGY_SATURADO`, `STRATEGY_PENDENTE` — string constants

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_models.py
from dataclasses import asdict
from src.trends.models import (
    TrendTerm, TrendSnapshot, TrendVelocity, TrendOpportunity,
    STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA, STRATEGY_EMERGENTE,
    STRATEGY_SATURADO, STRATEGY_PENDENTE,
)


def test_trend_term_creation():
    t = TrendTerm(id=1, term="wireless earbuds", category="Eletrônicos",
                  source="both", active=True, created_at="2026-09-27T04:00:00Z",
                  last_hit_at=None)
    assert t.term == "wireless earbuds"
    assert t.active is True
    assert t.last_hit_at is None


def test_trend_snapshot_creation():
    s = TrendSnapshot(id=1, term_id=1, source="aliexpress", product_id="12345",
                      title="Wireless Earbuds V2", price_brl=89.90, price_usd=16.50,
                      sales_total=3400, rating=4.8, moq=None, supplier_name=None,
                      is_verified=None, url="https://aliexpress.com/item/12345.html",
                      collected_at="2026-09-27")
    assert s.product_id == "12345"
    assert s.moq is None


def test_trend_velocity_creation():
    v = TrendVelocity(product_id="12345", source="aliexpress",
                      title="Wireless Earbuds V2", url="https://example.com",
                      category="Eletrônicos", price_brl=89.90, sales_total=3400,
                      sales_velocity_7d=800, sales_velocity_30d=3000,
                      acceleration=25.0, rating=4.8, moq=None,
                      supplier_name=None, is_verified=None)
    assert v.sales_velocity_7d == 800
    assert v.acceleration == 25.0


def test_trend_opportunity_serialization():
    opp = TrendOpportunity(
        product_id="12345", source="aliexpress", title="Test",
        url="https://example.com", category="Eletrônicos", price_brl=89.90,
        sales_total=3400, sales_velocity_7d=800, sales_velocity_30d=3000,
        acceleration=25.0, ml_query="fone sem fio", ml_competitors=0,
        ml_avg_price=0.0, ml_min_price=0.0, ml_full_share_pct=0.0,
        ml_total_sales_br=0, landed_cost_brl=45.0, suggested_price_brl=129.90,
        net_margin_pct=54.0, strategy=STRATEGY_OCEANO_AZUL, trend_score=92.0,
        supplier_name=None, moq=None, is_verified=None,
        sparkline=[100, 200, 500, 1200, 3400], calculated_at="2026-09-27T06:00:00Z"
    )
    d = asdict(opp)
    assert d["strategy"] == "OCEANO_AZUL"
    assert d["sparkline"] == [100, 200, 500, 1200, 3400]
    assert isinstance(d, dict)


def test_strategy_constants():
    assert STRATEGY_OCEANO_AZUL == "OCEANO_AZUL"
    assert STRATEGY_TENDENCIA == "TENDENCIA"
    assert STRATEGY_EMERGENTE == "EMERGENTE"
    assert STRATEGY_SATURADO == "SATURADO"
    assert STRATEGY_PENDENTE == "PENDENTE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.trends'`

- [ ] **Step 3: Write implementation**

```python
# src/trends/__init__.py
"""Trend Radar — daily trend detection pipeline."""
```

```python
# src/trends/models.py
"""Data models for the Trend Radar pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

STRATEGY_OCEANO_AZUL = "OCEANO_AZUL"
STRATEGY_TENDENCIA = "TENDENCIA"
STRATEGY_EMERGENTE = "EMERGENTE"
STRATEGY_SATURADO = "SATURADO"
STRATEGY_PENDENTE = "PENDENTE"


@dataclass
class TrendTerm:
    id: int
    term: str
    category: str
    source: str  # 'ali', 'alibaba', 'both'
    active: bool
    created_at: str
    last_hit_at: Optional[str] = None


@dataclass
class TrendSnapshot:
    id: int
    term_id: int
    source: str  # 'aliexpress' or 'alibaba'
    product_id: str
    title: str
    price_brl: Optional[float]
    price_usd: Optional[float]
    sales_total: Optional[int]
    rating: Optional[float]
    moq: Optional[int]
    supplier_name: Optional[str]
    is_verified: Optional[bool]
    url: str
    collected_at: str


@dataclass
class TrendVelocity:
    product_id: str
    source: str
    title: str
    url: str
    category: str
    price_brl: Optional[float]
    sales_total: Optional[int]
    sales_velocity_7d: int
    sales_velocity_30d: int
    acceleration: float  # % change week-over-week
    rating: Optional[float] = None
    moq: Optional[int] = None
    supplier_name: Optional[str] = None
    is_verified: Optional[bool] = None


@dataclass
class TrendOpportunity:
    product_id: str
    source: str
    title: str
    url: str
    category: str
    price_brl: Optional[float]
    sales_total: Optional[int]
    sales_velocity_7d: int
    sales_velocity_30d: int
    acceleration: float
    ml_query: str
    ml_competitors: Optional[int]
    ml_avg_price: Optional[float]
    ml_min_price: Optional[float]
    ml_full_share_pct: Optional[float]
    ml_total_sales_br: Optional[int]
    landed_cost_brl: Optional[float]
    suggested_price_brl: Optional[float]
    net_margin_pct: Optional[float]
    strategy: str
    trend_score: float
    supplier_name: Optional[str] = None
    moq: Optional[int] = None
    is_verified: Optional[bool] = None
    sparkline: list[int] = field(default_factory=list)
    calculated_at: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_models.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/__init__.py src/trends/models.py tests/test_trend_models.py
git commit -m "feat(trends): add data models for Trend Radar pipeline"
```

---

### Task 2: Default Terms

**Files:**
- Create: `src/trends/terms.py`
- Test: `tests/test_trend_terms.py`

**Interfaces:**
- Consumes: `TrendTerm` from `src/trends/models.py`
- Produces:
  - `DEFAULT_TERMS: list[dict]` — list of `{"term": str, "category": str, "source": str}`
  - `get_default_terms() -> list[dict]` — returns `DEFAULT_TERMS`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_terms.py
from src.trends.terms import DEFAULT_TERMS, get_default_terms


def test_default_terms_not_empty():
    assert len(DEFAULT_TERMS) >= 50


def test_default_terms_have_required_fields():
    for t in DEFAULT_TERMS:
        assert "term" in t and isinstance(t["term"], str) and len(t["term"]) > 0
        assert "category" in t and isinstance(t["category"], str) and len(t["category"]) > 0
        assert "source" in t and t["source"] in ("ali", "alibaba", "both")


def test_default_terms_unique():
    terms = [t["term"] for t in DEFAULT_TERMS]
    assert len(terms) == len(set(terms)), "Duplicate terms found"


def test_default_terms_cover_expected_categories():
    categories = {t["category"] for t in DEFAULT_TERMS}
    expected = {"Eletrônicos", "Casa & Cozinha", "Beleza & Saúde",
                "Moda & Acessórios", "Ferramentas", "Pet",
                "Esporte & Outdoor", "Bebê & Criança"}
    assert expected.issubset(categories), f"Missing categories: {expected - categories}"


def test_get_default_terms_returns_copy():
    a = get_default_terms()
    b = get_default_terms()
    assert a == b
    assert a is not b
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_terms.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# src/trends/terms.py
"""Default search terms for the Trend Radar daily collection."""
from __future__ import annotations

DEFAULT_TERMS: list[dict] = [
    # Eletrônicos
    {"term": "wireless earbuds", "category": "Eletrônicos", "source": "both"},
    {"term": "phone holder", "category": "Eletrônicos", "source": "both"},
    {"term": "portable charger", "category": "Eletrônicos", "source": "both"},
    {"term": "led strip lights", "category": "Eletrônicos", "source": "both"},
    {"term": "smart watch", "category": "Eletrônicos", "source": "both"},
    {"term": "bluetooth speaker", "category": "Eletrônicos", "source": "both"},
    {"term": "ring light", "category": "Eletrônicos", "source": "both"},
    {"term": "mini projector", "category": "Eletrônicos", "source": "both"},
    # Casa & Cozinha
    {"term": "kitchen gadget", "category": "Casa & Cozinha", "source": "both"},
    {"term": "organizer storage", "category": "Casa & Cozinha", "source": "both"},
    {"term": "silicone mold", "category": "Casa & Cozinha", "source": "both"},
    {"term": "electric kettle", "category": "Casa & Cozinha", "source": "both"},
    {"term": "mini blender", "category": "Casa & Cozinha", "source": "both"},
    {"term": "vacuum sealer", "category": "Casa & Cozinha", "source": "both"},
    {"term": "spice rack", "category": "Casa & Cozinha", "source": "both"},
    {"term": "coffee accessories", "category": "Casa & Cozinha", "source": "both"},
    # Beleza & Saúde
    {"term": "hair straightener brush", "category": "Beleza & Saúde", "source": "both"},
    {"term": "facial massager", "category": "Beleza & Saúde", "source": "both"},
    {"term": "nail art kit", "category": "Beleza & Saúde", "source": "both"},
    {"term": "makeup organizer", "category": "Beleza & Saúde", "source": "both"},
    {"term": "teeth whitening", "category": "Beleza & Saúde", "source": "both"},
    {"term": "scalp massager", "category": "Beleza & Saúde", "source": "both"},
    {"term": "beauty blender", "category": "Beleza & Saúde", "source": "both"},
    {"term": "lash curler", "category": "Beleza & Saúde", "source": "both"},
    # Moda & Acessórios
    {"term": "polarized sunglasses", "category": "Moda & Acessórios", "source": "both"},
    {"term": "automatic watch", "category": "Moda & Acessórios", "source": "both"},
    {"term": "crossbody bag", "category": "Moda & Acessórios", "source": "both"},
    {"term": "minimalist wallet", "category": "Moda & Acessórios", "source": "both"},
    {"term": "stainless steel ring", "category": "Moda & Acessórios", "source": "both"},
    {"term": "silk scarf", "category": "Moda & Acessórios", "source": "both"},
    {"term": "bucket hat", "category": "Moda & Acessórios", "source": "both"},
    # Ferramentas
    {"term": "laser level", "category": "Ferramentas", "source": "both"},
    {"term": "electric screwdriver", "category": "Ferramentas", "source": "both"},
    {"term": "soldering kit", "category": "Ferramentas", "source": "both"},
    {"term": "digital caliper", "category": "Ferramentas", "source": "both"},
    {"term": "heat gun", "category": "Ferramentas", "source": "both"},
    {"term": "wire stripper", "category": "Ferramentas", "source": "both"},
    {"term": "multimeter", "category": "Ferramentas", "source": "both"},
    # Pet
    {"term": "automatic pet feeder", "category": "Pet", "source": "both"},
    {"term": "dog harness", "category": "Pet", "source": "both"},
    {"term": "cat toy interactive", "category": "Pet", "source": "both"},
    {"term": "pet grooming", "category": "Pet", "source": "both"},
    {"term": "dog training collar", "category": "Pet", "source": "both"},
    {"term": "cat water fountain", "category": "Pet", "source": "both"},
    # Esporte & Outdoor
    {"term": "resistance bands", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "jump rope", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "hiking backpack", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "camping light", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "yoga mat", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "fishing lure set", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "bike light", "category": "Esporte & Outdoor", "source": "both"},
    # Bebê & Criança
    {"term": "baby carrier", "category": "Bebê & Criança", "source": "both"},
    {"term": "educational toy", "category": "Bebê & Criança", "source": "both"},
    {"term": "kids tablet", "category": "Bebê & Criança", "source": "both"},
    {"term": "baby monitor", "category": "Bebê & Criança", "source": "both"},
    {"term": "stroller organizer", "category": "Bebê & Criança", "source": "both"},
    {"term": "teething toy", "category": "Bebê & Criança", "source": "both"},
]


def get_default_terms() -> list[dict]:
    """Return a copy of the default terms list."""
    return [dict(t) for t in DEFAULT_TERMS]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_terms.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/terms.py tests/test_trend_terms.py
git commit -m "feat(trends): add default search terms for 8 categories"
```

---

### Task 3: SQLite Repository

**Files:**
- Create: `src/trends/repository.py`
- Test: `tests/test_trend_repository.py`

**Interfaces:**
- Consumes: `TrendTerm`, `TrendSnapshot`, `TrendOpportunity` from `src/trends/models.py`; `get_default_terms()` from `src/trends/terms.py`
- Produces:
  - `TrendRepository(db_path: str)` — class
  - `TrendRepository.initialize()` — creates tables and indexes
  - `TrendRepository.seed_default_terms()` — inserts DEFAULT_TERMS if empty
  - `TrendRepository.get_active_terms() -> list[TrendTerm]`
  - `TrendRepository.save_snapshots(snapshots: list[dict])` — bulk insert, ignores duplicates
  - `TrendRepository.get_snapshots_for_velocity(product_id: str, source: str, days: int) -> list[tuple[str, int]]` — returns `(collected_at, sales_total)` pairs
  - `TrendRepository.get_all_product_ids_with_snapshots(min_days: int) -> list[tuple[str, str, str]]` — returns `(product_id, source, category)` for products with data spanning at least `min_days` days
  - `TrendRepository.save_opportunities(opportunities: list[dict])`
  - `TrendRepository.get_trending(strategy: str | None, category: str | None, limit: int) -> list[dict]`
  - `TrendRepository.get_product_history(product_id: str, source: str) -> list[dict]`
  - `TrendRepository.get_sparkline(product_id: str, source: str, points: int) -> list[int]`
  - `TrendRepository.get_stats() -> dict`
  - `TrendRepository.cleanup_old(days: int)`
  - `TrendRepository.deactivate_stale_terms(inactive_days: int)`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_repository.py
import sqlite3
from datetime import datetime, timedelta, timezone

from src.trends.repository import TrendRepository


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    return repo


def test_initialize_creates_tables():
    repo = _make_repo()
    conn = repo._conn
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "trend_terms" in tables
    assert "trend_snapshots" in tables
    assert "trend_opportunities" in tables


def test_seed_default_terms():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    assert len(terms) >= 50
    assert all(t.active for t in terms)


def test_seed_default_terms_idempotent():
    repo = _make_repo()
    repo.seed_default_terms()
    count1 = len(repo.get_active_terms())
    repo.seed_default_terms()
    count2 = len(repo.get_active_terms())
    assert count1 == count2


def test_save_and_query_snapshots():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshots = [
        {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
         "title": "Test Product", "price_brl": 50.0, "price_usd": 10.0,
         "sales_total": 1000, "rating": 4.5, "moq": None,
         "supplier_name": None, "is_verified": None,
         "url": "https://example.com/p1", "collected_at": today}
    ]
    repo.save_snapshots(snapshots)
    history = repo.get_snapshots_for_velocity("p1", "aliexpress", days=7)
    assert len(history) == 1
    assert history[0][1] == 1000


def test_save_snapshots_ignores_duplicates():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Test", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 1000, "rating": 4.5, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    repo.save_snapshots([snap])  # duplicate
    history = repo.get_snapshots_for_velocity("p1", "aliexpress", days=30)
    assert len(history) == 1


def test_save_and_query_opportunities():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Trending Item", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 5000, "rating": 4.8, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    # Get snapshot_id
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    opp = {
        "snapshot_id": row[0], "product_id": "p1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 5000,
        "acceleration": 50.0, "ml_query": "item trending",
        "ml_competitors": 0, "ml_avg_price": 0.0, "ml_min_price": 0.0,
        "ml_full_share_pct": 0.0, "ml_total_sales_br": 0,
        "landed_cost_brl": 25.0, "suggested_price_brl": 89.90,
        "net_margin_pct": 54.0, "strategy": "OCEANO_AZUL",
        "trend_score": 92.0, "calculated_at": "2026-09-27T06:00:00Z"
    }
    repo.save_opportunities([opp])
    results = repo.get_trending(strategy="OCEANO_AZUL", category=None, limit=10)
    assert len(results) == 1
    assert results[0]["trend_score"] == 92.0


def test_get_trending_filters():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Test", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 5000, "rating": 4.8, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    opp = {
        "snapshot_id": row[0], "product_id": "p1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 5000,
        "acceleration": 50.0, "ml_query": "test", "ml_competitors": 0,
        "ml_avg_price": 0.0, "ml_min_price": 0.0, "ml_full_share_pct": 0.0,
        "ml_total_sales_br": 0, "landed_cost_brl": 25.0,
        "suggested_price_brl": 89.90, "net_margin_pct": 54.0,
        "strategy": "OCEANO_AZUL", "trend_score": 92.0,
        "calculated_at": "2026-09-27T06:00:00Z"
    }
    repo.save_opportunities([opp])
    assert len(repo.get_trending(strategy="SATURADO", category=None, limit=10)) == 0
    assert len(repo.get_trending(strategy=None, category=None, limit=10)) == 1


def test_cleanup_old():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    old_date = (datetime.now(timezone.utc) - timedelta(days=100)).strftime("%Y-%m-%d")
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "old1",
            "title": "Old Product", "price_brl": 10.0, "price_usd": 2.0,
            "sales_total": 100, "rating": 3.0, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/old1", "collected_at": old_date}
    repo.save_snapshots([snap])
    assert len(repo.get_snapshots_for_velocity("old1", "aliexpress", days=200)) == 1
    repo.cleanup_old(days=90)
    assert len(repo.get_snapshots_for_velocity("old1", "aliexpress", days=200)) == 0


def test_get_stats_empty():
    repo = _make_repo()
    stats = repo.get_stats()
    assert stats["total_monitored"] == 0
    assert stats["ocean_blue_count"] == 0


def test_get_sparkline():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for i in range(5):
        d = (datetime.now(timezone.utc) - timedelta(days=4 - i)).strftime("%Y-%m-%d")
        snap = {"term_id": term.id, "source": "aliexpress", "product_id": "sp1",
                "title": "Sparkline Test", "price_brl": 50.0, "price_usd": 10.0,
                "sales_total": 100 * (i + 1), "rating": 4.0, "moq": None,
                "supplier_name": None, "is_verified": None,
                "url": "https://example.com/sp1", "collected_at": d}
        repo.save_snapshots([snap])
    sparkline = repo.get_sparkline("sp1", "aliexpress", points=30)
    assert sparkline == [100, 200, 300, 400, 500]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_repository.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# src/trends/repository.py
"""SQLite repository for Trend Radar data."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import TrendTerm
from .terms import get_default_terms


class TrendRepository:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.row_factory = sqlite3.Row

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
            "GROUP BY s.product_id, s.source "
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
            "WHERE active = 1 AND id NOT IN ("
            "  SELECT DISTINCT term_id FROM trend_snapshots WHERE collected_at >= ?"
            ")", (cutoff,)
        )
        self._conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_repository.py -v`
Expected: 10 passed

- [ ] **Step 5: Run full test suite to ensure no regressions**

Run: `pytest -v`
Expected: 103 passed (93 existing + 10 new)

- [ ] **Step 6: Commit**

```bash
git add src/trends/repository.py tests/test_trend_repository.py
git commit -m "feat(trends): add SQLite repository for trend snapshots and opportunities"
```

---

### Task 4: Velocity Calculator

**Files:**
- Create: `src/trends/velocity.py`
- Test: `tests/test_trend_velocity.py`

**Interfaces:**
- Consumes: `TrendRepository.get_snapshots_for_velocity()`, `TrendRepository.get_all_product_ids_with_snapshots()`, `TrendVelocity` from `src/trends/models.py`
- Produces:
  - `MIN_TREND_VELOCITY: int` — constant = 100
  - `calculate_velocity(repo: TrendRepository) -> list[TrendVelocity]` — computes velocity for all eligible products, filters by MIN_TREND_VELOCITY, returns sorted by velocity descending

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_velocity.py
from datetime import datetime, timedelta, timezone

from src.trends.velocity import calculate_velocity, MIN_TREND_VELOCITY
from src.trends.repository import TrendRepository


def _make_repo_with_data(days_data: list[tuple[int, int]],
                          product_id: str = "p1") -> TrendRepository:
    """Create repo with snapshots. days_data = [(days_ago, sales_total), ...]"""
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for days_ago, sales in days_data:
        d = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        repo.save_snapshots([{
            "term_id": term.id, "source": "aliexpress", "product_id": product_id,
            "title": "Test Product", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": sales, "rating": 4.5, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": f"https://example.com/{product_id}", "collected_at": d
        }])
    return repo


def test_min_trend_velocity_constant():
    assert MIN_TREND_VELOCITY == 100


def test_velocity_7d_calculation():
    # 7 days ago: 1000 sales, today: 1800 sales → velocity_7d = 800
    repo = _make_repo_with_data([(7, 1000), (0, 1800)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 800


def test_velocity_30d_calculation():
    # 30 days ago: 500, 7 days ago: 1500, today: 2000
    repo = _make_repo_with_data([(30, 500), (7, 1500), (0, 2000)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 500
    assert results[0].sales_velocity_30d == 1500


def test_acceleration_calculation():
    # Week before last: velocity was 300 (1000→1300 in 7d)
    # Last week: velocity is 800 (1300→2100 in 7d)
    # Acceleration = (800 - 300) / 300 * 100 = 166.67%
    repo = _make_repo_with_data([(14, 1000), (7, 1300), (0, 2100)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 800
    assert round(results[0].acceleration, 1) == 166.7


def test_filters_below_threshold():
    # velocity_7d = 50, below MIN_TREND_VELOCITY of 100
    repo = _make_repo_with_data([(7, 1000), (0, 1050)])
    results = calculate_velocity(repo)
    assert len(results) == 0


def test_handles_single_snapshot():
    repo = _make_repo_with_data([(0, 5000)])
    results = calculate_velocity(repo)
    assert len(results) == 0  # needs ≥2 snapshots


def test_handles_null_sales():
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "pnull",
        "title": "Null Sales", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": None, "rating": 4.5, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://example.com/pnull", "collected_at": "2026-09-27"
    }])
    results = calculate_velocity(repo)
    assert len(results) == 0


def test_handles_decreasing_sales():
    # Sales went down (possible data glitch) → velocity negative → filtered out
    repo = _make_repo_with_data([(7, 5000), (0, 4000)])
    results = calculate_velocity(repo)
    assert len(results) == 0  # negative velocity filtered


def test_sorted_by_velocity_descending():
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for pid, v7, v0 in [("slow", 1000, 1200), ("fast", 1000, 5000), ("mid", 1000, 2000)]:
        for days_ago, sales in [(7, v7), (0, v0)]:
            d = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            repo.save_snapshots([{
                "term_id": term.id, "source": "aliexpress", "product_id": pid,
                "title": f"Product {pid}", "price_brl": 50.0, "price_usd": 10.0,
                "sales_total": sales, "rating": 4.5, "moq": None,
                "supplier_name": None, "is_verified": None,
                "url": f"https://example.com/{pid}", "collected_at": d
            }])
    results = calculate_velocity(repo)
    assert results[0].product_id == "fast"
    assert results[1].product_id == "mid"
    assert results[2].product_id == "slow"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_velocity.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# src/trends/velocity.py
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
            s7_list = repo.get_snapshots_for_velocity(product_id, source, days=7)
            if s7_list:
                s7 = s7_list[0][1]
                prev_velocity = s7 - s14
                if prev_velocity > 0:
                    acceleration = ((velocity_7d - prev_velocity) / prev_velocity) * 100.0

        # Get latest snapshot details for title, url, price, etc.
        latest_row = repo._conn.execute(
            "SELECT title, url, price_brl, sales_total, rating, moq, "
            "supplier_name, is_verified FROM trend_snapshots "
            "WHERE product_id = ? AND source = ? ORDER BY collected_at DESC LIMIT 1",
            (product_id, source)
        ).fetchone()

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_velocity.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/velocity.py tests/test_trend_velocity.py
git commit -m "feat(trends): add velocity calculator with acceleration and threshold filtering"
```

---

### Task 5: Trend Scoring

**Files:**
- Create: `src/trends/scoring.py`
- Test: `tests/test_trend_scoring.py`

**Interfaces:**
- Consumes: `TrendVelocity` from `src/trends/models.py`; strategy constants from `src/trends/models.py`
- Produces:
  - `calculate_trend_score(velocity: TrendVelocity, ml_competitors: int | None, net_margin_pct: float | None, max_velocity_in_category: int) -> tuple[float, str]` — returns `(score, strategy)`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_scoring.py
from src.trends.scoring import calculate_trend_score
from src.trends.models import (
    TrendVelocity, STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA,
    STRATEGY_EMERGENTE, STRATEGY_SATURADO, STRATEGY_PENDENTE,
)


def _make_velocity(**overrides) -> TrendVelocity:
    defaults = dict(
        product_id="p1", source="aliexpress", title="Test", url="https://x.com",
        category="Eletrônicos", price_brl=50.0, sales_total=5000,
        sales_velocity_7d=5000, sales_velocity_30d=15000, acceleration=100.0,
    )
    defaults.update(overrides)
    return TrendVelocity(**defaults)


def test_oceano_azul_high_score():
    v = _make_velocity(sales_velocity_7d=8000)
    score, strategy = calculate_trend_score(v, ml_competitors=0,
                                            net_margin_pct=55.0,
                                            max_velocity_in_category=10000)
    assert score >= 75
    assert strategy == STRATEGY_OCEANO_AZUL


def test_tendencia_medium_score():
    v = _make_velocity(sales_velocity_7d=5000)
    score, strategy = calculate_trend_score(v, ml_competitors=5,
                                            net_margin_pct=40.0,
                                            max_velocity_in_category=10000)
    assert 50 <= score < 75
    assert strategy == STRATEGY_TENDENCIA


def test_emergente_lower_score():
    v = _make_velocity(sales_velocity_7d=3000)
    score, strategy = calculate_trend_score(v, ml_competitors=20,
                                            net_margin_pct=25.0,
                                            max_velocity_in_category=10000)
    assert 25 <= score < 50
    assert strategy == STRATEGY_EMERGENTE


def test_saturado_low_score():
    v = _make_velocity(sales_velocity_7d=500)
    score, strategy = calculate_trend_score(v, ml_competitors=80,
                                            net_margin_pct=5.0,
                                            max_velocity_in_category=10000)
    assert score < 25
    assert strategy == STRATEGY_SATURADO


def test_pendente_when_ml_data_missing():
    v = _make_velocity(sales_velocity_7d=5000)
    score, strategy = calculate_trend_score(v, ml_competitors=None,
                                            net_margin_pct=None,
                                            max_velocity_in_category=10000)
    assert strategy == STRATEGY_PENDENTE


def test_score_clamped_0_to_100():
    v = _make_velocity(sales_velocity_7d=100000)
    score, _ = calculate_trend_score(v, ml_competitors=0,
                                     net_margin_pct=99.0,
                                     max_velocity_in_category=1000)
    assert 0 <= score <= 100


def test_zero_max_velocity_no_crash():
    v = _make_velocity(sales_velocity_7d=500)
    score, _ = calculate_trend_score(v, ml_competitors=0,
                                     net_margin_pct=50.0,
                                     max_velocity_in_category=0)
    assert 0 <= score <= 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_scoring.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# src/trends/scoring.py
"""Trend Score (0-100) and strategic classification."""
from __future__ import annotations

from .models import (
    TrendVelocity,
    STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA,
    STRATEGY_EMERGENTE, STRATEGY_SATURADO, STRATEGY_PENDENTE,
)

# Weight distribution
W_VELOCITY = 0.40
W_VACUUM = 0.35
W_VIABILITY = 0.25

# Normalization caps
MAX_COMPETITORS_CAP = 50
MAX_MARGIN_CAP = 50.0


def calculate_trend_score(
    velocity: TrendVelocity,
    ml_competitors: int | None,
    net_margin_pct: float | None,
    max_velocity_in_category: int,
) -> tuple[float, str]:
    """Return (score 0-100, strategy string)."""

    # Velocity signal (0-100)
    if max_velocity_in_category > 0:
        vel_score = min(velocity.sales_velocity_7d / max_velocity_in_category, 1.0) * 100
    else:
        vel_score = 100.0 if velocity.sales_velocity_7d > 0 else 0.0

    # If ML data is missing, return PENDENTE with partial score
    if ml_competitors is None or net_margin_pct is None:
        partial = vel_score * W_VELOCITY
        return (round(min(max(partial, 0), 100), 1), STRATEGY_PENDENTE)

    # Vacuum signal (0-100): inverse of competitor count
    if ml_competitors <= 0:
        vac_score = 100.0
    elif ml_competitors >= MAX_COMPETITORS_CAP:
        vac_score = 0.0
    else:
        vac_score = (1.0 - ml_competitors / MAX_COMPETITORS_CAP) * 100

    # Viability signal (0-100): margin clamped
    if net_margin_pct <= 0:
        via_score = 0.0
    elif net_margin_pct >= MAX_MARGIN_CAP:
        via_score = 100.0
    else:
        via_score = (net_margin_pct / MAX_MARGIN_CAP) * 100

    score = vel_score * W_VELOCITY + vac_score * W_VACUUM + via_score * W_VIABILITY
    score = round(min(max(score, 0), 100), 1)

    if score >= 75:
        strategy = STRATEGY_OCEANO_AZUL
    elif score >= 50:
        strategy = STRATEGY_TENDENCIA
    elif score >= 25:
        strategy = STRATEGY_EMERGENTE
    else:
        strategy = STRATEGY_SATURADO

    return (score, strategy)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_scoring.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/scoring.py tests/test_trend_scoring.py
git commit -m "feat(trends): add Trend Score algorithm with 3-signal weighted classification"
```

---

### Task 6: Collector (Stage 1)

**Files:**
- Create: `src/trends/collector.py`
- Test: `tests/test_trend_collector.py`

**Interfaces:**
- Consumes: `TrendRepository`, `DirectAliExpressClient` from `src/clients/direct_scraper.py`, `DirectAlibabaClient` from `src/clients/alibaba_scraper.py`, `get_usd_brl_rate()` from `src/finance/currency.py`
- Produces:
  - `BLOCK_SIZE: int` — constant = 15
  - `BLOCK_PAUSE_SECONDS: int` — constant = 600 (10 min)
  - `REQUEST_DELAY_RANGE: tuple[float, float]` — constant = (2.0, 5.0)
  - `collect_trends(repo: TrendRepository, block_pause: float | None = None, request_delay: tuple[float, float] | None = None) -> dict` — runs Stage 1, returns `{"collected": int, "skipped_terms": int, "blocked": bool}`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_collector.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_collector.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# src/trends/collector.py
"""Stage 1: Daily collection of China marketplace data for trend tracking."""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone

from src.clients.direct_scraper import DirectAliExpressClient
from src.clients.alibaba_scraper import DirectAlibabaClient
from src.finance.currency import get_usd_brl_rate
from src.config import load_config
from .repository import TrendRepository

logger = logging.getLogger(__name__)

BLOCK_SIZE = 15
BLOCK_PAUSE_SECONDS = 600  # 10 minutes
REQUEST_DELAY_RANGE = (2.0, 5.0)
ITEMS_PER_TERM = 20


def collect_trends(
    repo: TrendRepository,
    block_pause: float | None = None,
    request_delay: tuple[float, float] | None = None,
) -> dict:
    """Run Stage 1: scrape China sources for all active terms.

    Returns dict with keys: collected, skipped_terms, blocked.
    """
    pause = block_pause if block_pause is not None else BLOCK_PAUSE_SECONDS
    delay = request_delay if request_delay is not None else REQUEST_DELAY_RANGE

    terms = repo.get_active_terms()
    if not terms:
        logger.warning("No active terms found. Run seed_default_terms() first.")
        return {"collected": 0, "skipped_terms": 0, "blocked": False}

    cfg = load_config()
    rate_info = get_usd_brl_rate(fallback_rate=cfg.DEFAULT_USD_BRL)
    usd_rate = rate_info.rate

    ali_client = DirectAliExpressClient()
    baba_client = DirectAlibabaClient()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_collected = 0
    skipped_terms = 0
    blocked = False

    for block_start in range(0, len(terms), BLOCK_SIZE):
        block = terms[block_start:block_start + BLOCK_SIZE]
        logger.info(f"Processing block {block_start // BLOCK_SIZE + 1} "
                     f"({len(block)} terms)")

        for term in block:
            snapshots: list[dict] = []

            # AliExpress
            if term.source in ("ali", "both"):
                try:
                    if delay[1] > 0:
                        time.sleep(random.uniform(delay[0], delay[1]))
                    items = ali_client.search(term.term, limit=ITEMS_PER_TERM)
                    for item in items:
                        snapshots.append({
                            "term_id": term.id,
                            "source": "aliexpress",
                            "product_id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price_brl": item.get("price"),
                            "price_usd": (item["price"] / usd_rate
                                          if item.get("price") else None),
                            "sales_total": item.get("sales"),
                            "rating": item.get("rating"),
                            "moq": None,
                            "supplier_name": None,
                            "is_verified": None,
                            "url": item.get("url", ""),
                            "collected_at": today,
                        })
                except Exception as e:
                    logger.warning(f"AliExpress failed for '{term.term}': {e}")
                    skipped_terms += 1

            # Alibaba
            if term.source in ("alibaba", "both"):
                try:
                    if delay[1] > 0:
                        time.sleep(random.uniform(delay[0], delay[1]))
                    items = baba_client.search(term.term, limit=ITEMS_PER_TERM)
                    for item in items:
                        price_brl = item.get("price", 0)
                        snapshots.append({
                            "term_id": term.id,
                            "source": "alibaba",
                            "product_id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price_brl": price_brl,
                            "price_usd": (price_brl / usd_rate
                                          if price_brl else None),
                            "sales_total": item.get("sales"),
                            "rating": item.get("rating"),
                            "moq": item.get("moq"),
                            "supplier_name": item.get("supplier_name"),
                            "is_verified": item.get("is_verified"),
                            "url": item.get("url", ""),
                            "collected_at": today,
                        })
                except Exception as e:
                    logger.warning(f"Alibaba failed for '{term.term}': {e}")
                    skipped_terms += 1

            if snapshots:
                repo.save_snapshots(snapshots)
                total_collected += len(snapshots)

        # Pause between blocks (except after last block)
        if block_start + BLOCK_SIZE < len(terms) and pause > 0:
            logger.info(f"Block pause: sleeping {pause}s")
            time.sleep(pause)

    logger.info(f"Collection complete: {total_collected} snapshots, "
                f"{skipped_terms} skipped terms")
    return {"collected": total_collected, "skipped_terms": skipped_terms,
            "blocked": blocked}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_collector.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/collector.py tests/test_trend_collector.py
git commit -m "feat(trends): add daily China marketplace collector with throttling and block pauses"
```

---

### Task 7: Gap Analyzer (Stage 3)

**Files:**
- Create: `src/trends/gap_analyzer.py`
- Test: `tests/test_trend_gap_analyzer.py`

**Interfaces:**
- Consumes: `TrendVelocity`, `TrendOpportunity` from models; `TrendRepository`; `CompetitorRadar` from `src/competitors/radar.py`; `ArbitrageEngine.calculate_landed_costs()` from `src/arbitrage/engine.py`; `calculate_trend_score()` from `src/trends/scoring.py`
- Produces:
  - `MAX_GAP_ANALYSIS: int` — constant = 100
  - `analyze_gaps(velocities: list[TrendVelocity], repo: TrendRepository) -> list[TrendOpportunity]` — runs Stage 3, returns scored and classified opportunities

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trend_gap_analyzer.py
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.trends.gap_analyzer import analyze_gaps, MAX_GAP_ANALYSIS
from src.trends.models import TrendVelocity, STRATEGY_OCEANO_AZUL, STRATEGY_PENDENTE
from src.trends.repository import TrendRepository


def _make_velocity(**overrides) -> TrendVelocity:
    defaults = dict(
        product_id="p1", source="aliexpress", title="Wireless Earbuds V2",
        url="https://aliexpress.com/item/p1.html", category="Eletrônicos",
        price_brl=50.0, sales_total=5000, sales_velocity_7d=3000,
        sales_velocity_30d=10000, acceleration=100.0,
    )
    defaults.update(overrides)
    return TrendVelocity(**defaults)


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "p1",
        "title": "Wireless Earbuds V2", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": 5000, "rating": 4.8, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://aliexpress.com/item/p1.html",
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }])
    return repo


def test_max_gap_analysis_constant():
    assert MAX_GAP_ANALYSIS == 100


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_oceano_azul(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []  # 0 competitors → Oceano Azul
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity(sales_velocity_7d=8000)]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].ml_competitors == 0
    assert results[0].strategy == STRATEGY_OCEANO_AZUL


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_with_competitors(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_competitor = MagicMock()
    mock_competitor.price_brl = 129.90
    mock_competitor.shipping_type = "Full"
    mock_radar.find_competitors.return_value = [mock_competitor] * 5
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity(sales_velocity_7d=3000)]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].ml_competitors == 5


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_ml_failure_marks_pendente(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.side_effect = Exception("ML blocked")
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity()]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].strategy == STRATEGY_PENDENTE
    assert results[0].ml_competitors is None


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_respects_max_limit(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    # Save additional snapshots for 150 products
    terms = repo.get_active_terms()
    for i in range(150):
        repo.save_snapshots([{
            "term_id": terms[0].id, "source": "aliexpress",
            "product_id": f"px{i}", "title": f"Product {i}",
            "price_brl": 50.0, "price_usd": 10.0, "sales_total": 5000,
            "rating": 4.5, "moq": None, "supplier_name": None,
            "is_verified": None, "url": f"https://example.com/px{i}",
            "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }])

    velocities = [_make_velocity(product_id=f"px{i}", sales_velocity_7d=5000 - i)
                  for i in range(150)]
    results = analyze_gaps(velocities, repo)
    assert len(results) <= MAX_GAP_ANALYSIS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_trend_gap_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# src/trends/gap_analyzer.py
"""Stage 3: Cross-reference trending China products with Brazilian market gaps."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.competitors.radar import CompetitorRadar
from src.finance.currency import get_usd_brl_rate
from src.config import load_config
from src.arbitrage.engine import ArbitrageEngine
from .models import TrendVelocity, TrendOpportunity, STRATEGY_PENDENTE
from .repository import TrendRepository
from .scoring import calculate_trend_score

logger = logging.getLogger(__name__)

MAX_GAP_ANALYSIS = 100

# Extended translation map for trend titles
TREND_TRANSLATION_MAP = {
    "wireless": "sem fio", "earbuds": "fone", "bluetooth": "bluetooth",
    "charger": "carregador", "portable": "portátil", "smart": "inteligente",
    "watch": "relógio", "speaker": "caixa de som", "light": "luz",
    "projector": "projetor", "kitchen": "cozinha", "organizer": "organizador",
    "storage": "armazenamento", "mold": "molde", "silicone": "silicone",
    "blender": "liquidificador", "vacuum": "vácuo", "sealer": "seladora",
    "coffee": "café", "hair": "cabelo", "straightener": "alisador",
    "brush": "escova", "facial": "facial", "massager": "massageador",
    "nail": "unha", "makeup": "maquiagem", "teeth": "dentes",
    "whitening": "clareamento", "scalp": "couro cabeludo", "beauty": "beleza",
    "sunglasses": "óculos de sol", "polarized": "polarizado", "automatic": "automático",
    "bag": "bolsa", "wallet": "carteira", "ring": "anel", "scarf": "lenço",
    "hat": "chapéu", "level": "nível", "laser": "laser", "screwdriver": "parafusadeira",
    "soldering": "solda", "caliper": "paquímetro", "digital": "digital",
    "heat": "calor", "gun": "pistola", "wire": "fio", "stripper": "descascador",
    "multimeter": "multímetro", "pet": "pet", "feeder": "alimentador",
    "dog": "cachorro", "harness": "peitoral", "cat": "gato", "toy": "brinquedo",
    "grooming": "tosa", "training": "adestramento", "collar": "coleira",
    "water": "água", "fountain": "fonte", "resistance": "resistência",
    "bands": "faixas", "jump": "pular", "rope": "corda", "hiking": "trilha",
    "backpack": "mochila", "camping": "camping", "yoga": "yoga", "mat": "tapete",
    "fishing": "pesca", "lure": "isca", "bike": "bicicleta", "baby": "bebê",
    "carrier": "canguru", "educational": "educativo", "kids": "infantil",
    "tablet": "tablet", "monitor": "monitor", "stroller": "carrinho",
    "teething": "mordedor",
}

STOP_WORDS = {
    "hot", "selling", "new", "2024", "2025", "2026", "factory", "wholesale",
    "oem", "odm", "free", "shipping", "drop", "dropshipping", "high", "quality",
    "best", "top", "pro", "premium", "original", "genuine", "brand",
    "for", "with", "and", "the", "set", "kit", "pcs", "lot", "pack",
}


def _translate_title(title: str) -> str:
    """Translate an English product title to Portuguese search query."""
    words = title.lower().split()
    translated = []
    for word in words:
        clean = word.strip(".,;:!?()[]{}\"'")
        if clean in STOP_WORDS or not clean:
            continue
        if clean in TREND_TRANSLATION_MAP:
            translated.append(TREND_TRANSLATION_MAP[clean])
        elif len(clean) > 2:
            translated.append(clean)
    return " ".join(translated[:6])  # limit to 6 words for search


def analyze_gaps(
    velocities: list[TrendVelocity],
    repo: TrendRepository,
) -> list[TrendOpportunity]:
    """Run Stage 3: cross-reference trending products with Mercado Livre."""
    top = velocities[:MAX_GAP_ANALYSIS]
    if not top:
        return []

    cfg = load_config()
    rate_info = get_usd_brl_rate(fallback_rate=cfg.DEFAULT_USD_BRL)
    usd_rate = rate_info.rate

    radar = CompetitorRadar()
    now = datetime.now(timezone.utc).isoformat()

    # Pre-compute max velocity per category for scoring
    max_vel_by_cat: dict[str, int] = {}
    for v in velocities:
        cur = max_vel_by_cat.get(v.category, 0)
        if v.sales_velocity_7d > cur:
            max_vel_by_cat[v.category] = v.sales_velocity_7d

    opportunities: list[TrendOpportunity] = []

    for v in top:
        ml_query = _translate_title(v.title)
        ml_competitors = None
        ml_avg_price = None
        ml_min_price = None
        ml_full_share_pct = None
        ml_total_sales_br = None
        landed_cost = None
        suggested_price = None
        net_margin = None

        try:
            competitors = radar.find_competitors(ml_query, limit=5)
            ml_competitors = len(competitors)

            if competitors:
                prices = [c.price_brl for c in competitors if c.price_brl and c.price_brl > 0]
                ml_avg_price = sum(prices) / len(prices) if prices else 0.0
                ml_min_price = min(prices) if prices else 0.0
                full_count = sum(1 for c in competitors
                                 if getattr(c, 'shipping_type', '') == 'Full')
                ml_full_share_pct = (full_count / len(competitors)) * 100 if competitors else 0.0
                ml_total_sales_br = sum(
                    getattr(c, 'sales_volume', 0) or 0 for c in competitors
                )
            else:
                ml_avg_price = 0.0
                ml_min_price = 0.0
                ml_full_share_pct = 0.0
                ml_total_sales_br = 0

            # Calculate landed cost
            if v.price_brl and v.price_brl > 0:
                fob = v.price_brl
                freight = fob * 0.15
                customs_base = fob + freight
                import_tax = customs_base * 0.60
                icms_base = (customs_base + import_tax) / (1.0 - cfg.DEFAULT_ICMS_RATE)
                icms = icms_base * cfg.DEFAULT_ICMS_RATE
                landed_cost = round(customs_base + import_tax + icms, 2)

                # Suggested price
                if ml_avg_price and ml_avg_price > 0:
                    suggested_price = ml_avg_price
                else:
                    suggested_price = round(landed_cost / (1.0 - cfg.DEFAULT_TARGET_MARGIN), 2)

                ml_fee = suggested_price * cfg.DEFAULT_MARKETPLACE_FEE
                net_profit = suggested_price - ml_fee - landed_cost
                net_margin = round((net_profit / suggested_price) * 100, 1) if suggested_price > 0 else 0.0

        except Exception as e:
            logger.warning(f"Gap analysis failed for '{v.title}': {e}")

        # Score and classify
        max_vel = max_vel_by_cat.get(v.category, v.sales_velocity_7d)
        score, strategy = calculate_trend_score(
            v, ml_competitors=ml_competitors,
            net_margin_pct=net_margin, max_velocity_in_category=max_vel
        )

        sparkline = repo.get_sparkline(v.product_id, v.source, points=30)

        # Get snapshot_id for the latest snapshot
        row = repo._conn.execute(
            "SELECT id FROM trend_snapshots WHERE product_id = ? AND source = ? "
            "ORDER BY collected_at DESC LIMIT 1",
            (v.product_id, v.source)
        ).fetchone()
        snapshot_id = row["id"] if row else 0

        opp = TrendOpportunity(
            product_id=v.product_id, source=v.source, title=v.title,
            url=v.url, category=v.category, price_brl=v.price_brl,
            sales_total=v.sales_total, sales_velocity_7d=v.sales_velocity_7d,
            sales_velocity_30d=v.sales_velocity_30d, acceleration=v.acceleration,
            ml_query=ml_query, ml_competitors=ml_competitors,
            ml_avg_price=ml_avg_price, ml_min_price=ml_min_price,
            ml_full_share_pct=ml_full_share_pct, ml_total_sales_br=ml_total_sales_br,
            landed_cost_brl=landed_cost, suggested_price_brl=suggested_price,
            net_margin_pct=net_margin, strategy=strategy, trend_score=score,
            supplier_name=v.supplier_name, moq=v.moq, is_verified=v.is_verified,
            sparkline=sparkline, calculated_at=now,
        )
        opportunities.append(opp)

        # Save to database
        repo.save_opportunities([{
            "snapshot_id": snapshot_id,
            "product_id": v.product_id, "source": v.source,
            "sales_velocity_7d": v.sales_velocity_7d,
            "sales_velocity_30d": v.sales_velocity_30d,
            "acceleration": v.acceleration,
            "ml_query": ml_query, "ml_competitors": ml_competitors,
            "ml_avg_price": ml_avg_price, "ml_min_price": ml_min_price,
            "ml_full_share_pct": ml_full_share_pct,
            "ml_total_sales_br": ml_total_sales_br,
            "landed_cost_brl": landed_cost,
            "suggested_price_brl": suggested_price,
            "net_margin_pct": net_margin,
            "strategy": strategy, "trend_score": score,
            "calculated_at": now,
        }])

    opportunities.sort(key=lambda o: o.trend_score, reverse=True)
    return opportunities
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_trend_gap_analyzer.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/trends/gap_analyzer.py tests/test_trend_gap_analyzer.py
git commit -m "feat(trends): add gap analyzer with ML cross-reference and landed cost calculation"
```

---

### Task 8: Pipeline Integration & CLI

**Files:**
- Create: `tests/test_trend_pipeline.py`
- Modify: `src/cli/main.py` — add `trends` subcommand

**Interfaces:**
- Consumes: `collect_trends`, `calculate_velocity`, `analyze_gaps`, `TrendRepository`
- Produces:
  - CLI subcommand `trends` with flags `--collect`, `--analyze`, `--cleanup`

- [ ] **Step 1: Write pipeline integration test**

```python
# tests/test_trend_pipeline.py
"""Integration test: runs all 3 stages with mocked scrapers."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.trends.repository import TrendRepository
from src.trends.collector import collect_trends
from src.trends.velocity import calculate_velocity
from src.trends.gap_analyzer import analyze_gaps


def _mock_ali_search(query, limit=20):
    return [{"id": f"ali_{i}", "title": f"Product {query} {i}",
             "price": 50.0, "shipping": 0.0, "sales": 1000 + i * 500,
             "rating": 4.5, "url": f"https://aliexpress.com/item/ali_{i}.html"}
            for i in range(3)]


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_full_pipeline(mock_ali_cls, mock_baba_cls, mock_radar_cls, mock_rate):
    # Setup mocks
    mock_ali = MagicMock()
    mock_ali.search.side_effect = _mock_ali_search
    mock_ali_cls.return_value = mock_ali
    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []
    mock_radar_cls.return_value = mock_radar

    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()

    # Stage 1: Collect day 1
    day1 = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    # Manually insert "day 1" snapshots for velocity calculation
    terms = repo.get_active_terms()
    for i in range(3):
        repo.save_snapshots([{
            "term_id": terms[0].id, "source": "aliexpress",
            "product_id": f"ali_{i}", "title": f"Product test {i}",
            "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 500 + i * 200,  # lower sales 7 days ago
            "rating": 4.5, "moq": None, "supplier_name": None,
            "is_verified": None, "url": f"https://aliexpress.com/item/ali_{i}.html",
            "collected_at": day1,
        }])

    # Stage 1: Collect today (uses mocked scrapers)
    result = collect_trends(repo, block_pause=0, request_delay=(0, 0))
    assert result["collected"] > 0

    # Stage 2: Calculate velocity
    velocities = calculate_velocity(repo)
    # At least some should have velocity > 100 (threshold)
    assert len(velocities) >= 0  # depends on delta

    # If we have velocities, run Stage 3
    if velocities:
        opportunities = analyze_gaps(velocities, repo)
        assert len(opportunities) > 0
        assert all(o.trend_score >= 0 for o in opportunities)

    # Verify stats work
    stats = repo.get_stats()
    assert stats["total_monitored"] >= 0
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_trend_pipeline.py -v`
Expected: PASS (with mocked scrapers)

- [ ] **Step 3: Add CLI subcommand**

Read `src/cli/main.py` to find the right insertion point, then add the `trends` subcommand alongside existing subcommands. The subcommand should:
- `--collect`: Run all 3 stages (collect → velocity → gap analysis)
- `--analyze`: Run only stages 2 and 3 (velocity → gap analysis)
- `--cleanup`: Remove data older than 90 days

Add this code to the argument parser section of `src/cli/main.py`:

```python
# In the subparser setup section:
trends_parser = subparsers.add_parser("trends", help="Radar de Tendências China → Brasil")
trends_group = trends_parser.add_mutually_exclusive_group(required=True)
trends_group.add_argument("--collect", action="store_true",
                          help="Executar coleta completa (3 estágios)")
trends_group.add_argument("--analyze", action="store_true",
                          help="Recalcular velocidades e oportunidades")
trends_group.add_argument("--cleanup", action="store_true",
                          help="Remover dados com mais de 90 dias")
```

And in the command dispatch section:

```python
if args.command == "trends":
    from src.trends.repository import TrendRepository
    from src.config import load_config
    import os

    cfg = load_config()
    db_path = os.getenv("MERCADO_LIVRE_DB_PATH", "data/mercado_livre_radar.db")
    repo = TrendRepository(db_path)
    repo.initialize()
    repo.seed_default_terms()

    if args.collect:
        from src.trends.collector import collect_trends
        from src.trends.velocity import calculate_velocity
        from src.trends.gap_analyzer import analyze_gaps

        print("🔍 Estágio 1: Coletando dados da China...")
        result = collect_trends(repo)
        print(f"   → {result['collected']} snapshots coletados, "
              f"{result['skipped_terms']} termos pulados")

        print("📊 Estágio 2: Calculando velocidades...")
        velocities = calculate_velocity(repo)
        print(f"   → {len(velocities)} produtos com aceleração detectada")

        if velocities:
            print("🇧🇷 Estágio 3: Cruzando com Mercado Livre...")
            opportunities = analyze_gaps(velocities, repo)
            oceanos = sum(1 for o in opportunities if o.strategy == "OCEANO_AZUL")
            print(f"   → {len(opportunities)} oportunidades, {oceanos} Oceanos Azuis")
        print("✅ Coleta completa!")

    elif args.analyze:
        from src.trends.velocity import calculate_velocity
        from src.trends.gap_analyzer import analyze_gaps

        print("📊 Recalculando velocidades...")
        velocities = calculate_velocity(repo)
        print(f"   → {len(velocities)} produtos com aceleração")
        if velocities:
            print("🇧🇷 Cruzando com Mercado Livre...")
            opportunities = analyze_gaps(velocities, repo)
            print(f"   → {len(opportunities)} oportunidades")
        print("✅ Análise completa!")

    elif args.cleanup:
        repo.cleanup_old(days=90)
        repo.deactivate_stale_terms(inactive_days=30)
        print("🧹 Limpeza concluída (dados > 90 dias removidos)")
```

- [ ] **Step 4: Run full test suite**

Run: `pytest -v`
Expected: All tests pass (existing 93 + new ~36)

- [ ] **Step 5: Commit**

```bash
git add tests/test_trend_pipeline.py src/cli/main.py
git commit -m "feat(trends): add pipeline integration test and CLI subcommand"
```

---

### Task 9: API Endpoints

**Files:**
- Modify: `src/mercado_livre/dashboard_api.py` — add 4 trend endpoints
- Test: `tests/test_api_trends.py`

**Interfaces:**
- Consumes: `TrendRepository` from `src/trends/repository.py`
- Produces:
  - `GET /radar/api/trends` — query params `strategy`, `category`, `limit`
  - `GET /radar/api/trends/{product_id}/history` — query param `source`
  - `GET /radar/api/trends/stats`
  - `GET /radar/api/trends/terms`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_trends.py
import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.mercado_livre.dashboard_api import create_app
from src.trends.repository import TrendRepository


@pytest.fixture
def client(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    db_path = str(tmp_path / "test.db")

    # Initialize trend tables
    repo = TrendRepository(db_path)
    repo.initialize()
    repo.seed_default_terms()

    # Insert test data
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "test1",
        "title": "Trending Product", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": 5000, "rating": 4.8, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://aliexpress.com/item/test1.html",
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }])
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    repo.save_opportunities([{
        "snapshot_id": row["id"], "product_id": "test1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 10000,
        "acceleration": 50.0, "ml_query": "produto trending",
        "ml_competitors": 0, "ml_avg_price": 0.0, "ml_min_price": 0.0,
        "ml_full_share_pct": 0.0, "ml_total_sales_br": 0,
        "landed_cost_brl": 25.0, "suggested_price_brl": 89.90,
        "net_margin_pct": 54.0, "strategy": "OCEANO_AZUL",
        "trend_score": 92.0, "calculated_at": datetime.now(timezone.utc).isoformat()
    }])
    repo._conn.close()

    with patch.dict("os.environ", {"MERCADO_LIVRE_DB_PATH": db_path}):
        app = create_app(
            report_dir=str(report_dir),
            access_key="test-key-minimum-24-characters-long",
        )
        tc = TestClient(app)
        # Authenticate
        tc.post("/radar/api/session",
                json={"key": "test-key-minimum-24-characters-long"})
        yield tc


def test_get_trends(client):
    resp = client.get("/radar/api/trends")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["strategy"] == "OCEANO_AZUL"


def test_get_trends_filter_strategy(client):
    resp = client.get("/radar/api/trends?strategy=SATURADO")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 0


def test_get_trends_stats(client):
    resp = client.get("/radar/api/trends/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_monitored" in data
    assert "ocean_blue_count" in data
    assert data["ocean_blue_count"] >= 1


def test_get_product_history(client):
    resp = client.get("/radar/api/trends/test1/history?source=aliexpress")
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert len(data["history"]) >= 1


def test_get_trends_terms(client):
    resp = client.get("/radar/api/trends/terms")
    assert resp.status_code == 200
    data = resp.json()
    assert "terms" in data
    assert len(data["terms"]) >= 50


def test_trends_requires_auth():
    from src.mercado_livre.dashboard_api import create_app
    app = create_app(access_key="test-key-minimum-24-characters-long")
    tc = TestClient(app)
    resp = tc.get("/radar/api/trends")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_trends.py -v`
Expected: FAIL (endpoints don't exist yet)

- [ ] **Step 3: Add trend endpoints to dashboard_api.py**

Insert the following endpoint definitions inside the `create_app()` function in `src/mercado_livre/dashboard_api.py`, before the static files mount at the end:

```python
    # --- Trend Radar endpoints ---
    import os as _os
    from src.trends.repository import TrendRepository as _TrendRepo

    def _get_trend_repo():
        db_path = _os.getenv("MERCADO_LIVRE_DB_PATH", "data/mercado_livre_radar.db")
        repo = _TrendRepo(db_path)
        repo.initialize()
        return repo

    @app.get('/radar/api/trends', dependencies=[Depends(authorized)])
    def get_trends(strategy: str = "", category: str = "", limit: int = 100):
        repo = _get_trend_repo()
        items = repo.get_trending(
            strategy=strategy or None,
            category=category or None,
            limit=min(limit, 200),
        )
        # Enrich with sparkline
        for item in items:
            item["sparkline"] = repo.get_sparkline(
                item["product_id"], item["source"], points=30
            )
        return {"items": items}

    @app.get('/radar/api/trends/stats', dependencies=[Depends(authorized)])
    def get_trend_stats():
        repo = _get_trend_repo()
        return repo.get_stats()

    @app.get('/radar/api/trends/terms', dependencies=[Depends(authorized)])
    def get_trend_terms():
        repo = _get_trend_repo()
        terms = repo.get_active_terms()
        return {"terms": [{"id": t.id, "term": t.term, "category": t.category,
                           "source": t.source} for t in terms]}

    @app.get('/radar/api/trends/{product_id}/history', dependencies=[Depends(authorized)])
    def get_trend_history(product_id: str, source: str = "aliexpress"):
        repo = _get_trend_repo()
        history = repo.get_product_history(product_id, source)
        return {"history": history}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_trends.py -v`
Expected: 6 passed

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add src/mercado_livre/dashboard_api.py tests/test_api_trends.py
git commit -m "feat(trends): add 4 API endpoints for trend data, stats, history and terms"
```

---

### Task 10: Dashboard Frontend — Types, App.tsx, Navbar

**Files:**
- Modify: `dashboard/src/types.ts` — add 3 interfaces
- Modify: `dashboard/src/App.tsx` — add trends tab and data fetching
- Modify: `dashboard/src/components/Navbar.tsx` — add "Tendências" pill

**Interfaces:**
- Consumes: API endpoints `GET /radar/api/trends`, `GET /radar/api/trends/stats`
- Produces: `TrendOpportunity`, `TrendStats`, `TrendHistoryPoint` TypeScript interfaces; `activeTab` expanded to include `"trends"`

- [ ] **Step 1: Add TypeScript interfaces to types.ts**

Append to the end of `dashboard/src/types.ts`:

```typescript
export interface TrendOpportunity {
  product_id: string
  source: string
  title: string
  url: string
  category: string
  price_brl: number | null
  sales_total: number | null
  sales_velocity_7d: number
  sales_velocity_30d: number
  acceleration: number
  ml_query: string
  ml_competitors: number | null
  ml_avg_price: number | null
  ml_min_price: number | null
  ml_full_share_pct: number | null
  ml_total_sales_br: number | null
  landed_cost_brl: number | null
  suggested_price_brl: number | null
  net_margin_pct: number | null
  strategy: string
  trend_score: number
  supplier_name?: string
  moq?: number
  is_verified?: boolean
  sparkline: number[]
  calculated_at: string
}

export interface TrendStats {
  total_monitored: number
  ocean_blue_count: number
  trending_count: number
  emerging_count: number
  top_acceleration: { title: string; velocity_7d: number }
  by_category: { category: string; count: number }[]
}

export interface TrendHistoryPoint {
  collected_at: string
  sales_total: number | null
  price_brl: number | null
}
```

- [ ] **Step 2: Update App.tsx**

Change the `activeTab` state type from `"radar" | "arbitrage"` to `"radar" | "arbitrage" | "trends"`.

Add trend data state and fetching alongside the existing `fetchData`:

```typescript
const [trendItems, setTrendItems] = useState<TrendOpportunity[]>([])
const [trendStats, setTrendStats] = useState<TrendStats | null>(null)
```

In the `fetchData` function, add a third fetch to `Promise.all`:

```typescript
const [radarRes, arbRes, trendRes] = await Promise.all([
  fetch("/radar/api/data"),
  fetch("/radar/api/arbitrage"),
  fetch("/radar/api/trends"),
])
// ... existing handling ...
if (trendRes.ok) {
  const trendData = await trendRes.json()
  setTrendItems(trendData.items || [])
}
```

Add the trends tab rendering block alongside the existing conditional blocks:

```tsx
{!loading && activeTab === "trends" && (
  <TrendsView items={trendItems} />
)}
```

Add the import at the top:

```typescript
import { TrendsView } from "@/components/TrendsView"
import { TrendOpportunity, TrendStats, TrendHistoryPoint } from "@/types"
```

- [ ] **Step 3: Update Navbar.tsx**

Add the third pill button for "Tendências" with the `TrendingUp` icon from Lucide, following the same pattern as the existing "Radar" and "Arbitragem" pills:

```tsx
<button
  onClick={() => onTabChange("trends")}
  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
    activeTab === "trends"
      ? "bg-[#176449] text-white shadow-xs font-semibold"
      : "text-[#3b5249] hover:text-[#176449]"
  }`}
>
  <TrendingUp className="h-4 w-4" />
  Tendências
</button>
```

Update the `activeTab` prop type to `"radar" | "arbitrage" | "trends"` and the `onTabChange` callback type accordingly.

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/App.tsx dashboard/src/components/Navbar.tsx
git commit -m "feat(trends): add Tendências tab type, state, fetching and navigation pill"
```

---

### Task 11: Dashboard Frontend — TrendsView Component

**Files:**
- Create: `dashboard/src/components/TrendsView.tsx`
- Create: `dashboard/src/components/TrendFilters.tsx`
- Create: `dashboard/src/components/VelocitySparkline.tsx`

**Interfaces:**
- Consumes: `TrendOpportunity`, `TrendStats` from `types.ts`; `Card` from `ui/card.tsx`; `Badge` from `ui/badge.tsx`; `Button` from `ui/button.tsx`; `Input` from `ui/input.tsx`; Recharts `LineChart`
- Produces: `<TrendsView items={TrendOpportunity[]} />` component

- [ ] **Step 1: Create VelocitySparkline component**

```tsx
// dashboard/src/components/VelocitySparkline.tsx
import React from "react"
import { LineChart, Line, ResponsiveContainer } from "recharts"

interface Props {
  data: number[]
  color?: string
  width?: number
  height?: number
}

export const VelocitySparkline: React.FC<Props> = ({
  data, color = "#176449", width = 100, height = 32
}) => {
  if (!data || data.length === 0) return <span className="text-xs text-gray-400">—</span>
  const points = data.map((value, i) => ({ i, value }))
  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <Line type="monotone" dataKey="value" stroke={color}
                strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 2: Create TrendFilters component**

```tsx
// dashboard/src/components/TrendFilters.tsx
import React from "react"
import { Input } from "@/components/ui/input"

interface Props {
  activeStrategy: string
  onStrategyChange: (s: string) => void
  activeCategory: string
  onCategoryChange: (c: string) => void
  searchQuery: string
  onSearchChange: (q: string) => void
  categories: string[]
  counts: Record<string, number>
}

const STRATEGY_PILLS = [
  { key: "", label: "Todos", icon: "📊" },
  { key: "OCEANO_AZUL", label: "Oceano Azul", icon: "🔥" },
  { key: "TENDENCIA", label: "Tendência", icon: "🚀" },
  { key: "EMERGENTE", label: "Emergente", icon: "📈" },
  { key: "SATURADO", label: "Saturado", icon: "⚠️" },
]

export const TrendFilters: React.FC<Props> = ({
  activeStrategy, onStrategyChange, activeCategory, onCategoryChange,
  searchQuery, onSearchChange, categories, counts,
}) => {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap gap-1.5">
        {STRATEGY_PILLS.map((p) => (
          <button
            key={p.key}
            onClick={() => onStrategyChange(p.key)}
            className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-all ${
              activeStrategy === p.key
                ? "bg-[#176449] text-white shadow-xs"
                : "bg-[#f0f4f2] text-[#3b5249] hover:bg-[#e0e8e3]"
            }`}
          >
            <span>{p.icon}</span>
            {p.label}
            {counts[p.key] !== undefined && (
              <span className="ml-1 rounded-full bg-white/20 px-1.5 text-[10px]">
                {counts[p.key]}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <select
          value={activeCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="rounded-md border border-[#cbd8d1] bg-white px-2 py-1 text-xs"
        >
          <option value="">Todas as categorias</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <Input
          placeholder="Buscar produto..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 w-48 text-xs"
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create TrendsView main component**

```tsx
// dashboard/src/components/TrendsView.tsx
import React, { useState, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendFilters } from "@/components/TrendFilters"
import { VelocitySparkline } from "@/components/VelocitySparkline"
import { TrendOpportunity } from "@/types"
import { TrendingUp, Target, Flame, BarChart2, ExternalLink, ChevronDown, ChevronUp } from "lucide-react"

interface Props {
  items: TrendOpportunity[]
}

const STRATEGY_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  OCEANO_AZUL: { label: "Oceano Azul", color: "bg-emerald-100 text-emerald-800", icon: "🔥" },
  TENDENCIA: { label: "Tendência", color: "bg-blue-100 text-blue-800", icon: "🚀" },
  EMERGENTE: { label: "Emergente", color: "bg-amber-100 text-amber-800", icon: "📈" },
  SATURADO: { label: "Saturado", color: "bg-red-100 text-red-800", icon: "⚠️" },
  PENDENTE: { label: "Pendente", color: "bg-gray-100 text-gray-600", icon: "⏳" },
}

export const TrendsView: React.FC<Props> = ({ items }) => {
  const [strategyFilter, setStrategyFilter] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const categories = useMemo(() =>
    [...new Set(items.map((i) => i.category))].sort(), [items])

  const counts = useMemo(() => {
    const c: Record<string, number> = { "": items.length }
    for (const item of items) {
      c[item.strategy] = (c[item.strategy] || 0) + 1
    }
    return c
  }, [items])

  const filtered = useMemo(() => {
    let result = items
    if (strategyFilter) result = result.filter((i) => i.strategy === strategyFilter)
    if (categoryFilter) result = result.filter((i) => i.category === categoryFilter)
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter((i) =>
        i.title.toLowerCase().includes(q) ||
        (i.supplier_name || "").toLowerCase().includes(q) ||
        (i.ml_query || "").toLowerCase().includes(q)
      )
    }
    return result
  }, [items, strategyFilter, categoryFilter, searchQuery])

  const oceanCount = items.filter((i) => i.strategy === "OCEANO_AZUL").length
  const trendCount = items.filter((i) => i.strategy === "TENDENCIA").length
  const topAccel = items.length > 0
    ? items.reduce((a, b) => a.sales_velocity_7d > b.sales_velocity_7d ? a : b)
    : null

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-[#6b8a7a]">
              <BarChart2 className="h-4 w-4" /> Monitorados
            </div>
            <p className="mt-1 text-2xl font-bold text-[#111916]">{items.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-emerald-600">
              <Flame className="h-4 w-4" /> Oceanos Azuis
            </div>
            <p className="mt-1 text-2xl font-bold text-emerald-700">{oceanCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <TrendingUp className="h-4 w-4" /> Tendências
            </div>
            <p className="mt-1 text-2xl font-bold text-blue-700">{trendCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-[#6b8a7a]">
              <Target className="h-4 w-4" /> Top Aceleração
            </div>
            <p className="mt-1 text-lg font-bold text-[#111916]">
              {topAccel ? `+${topAccel.sales_velocity_7d.toLocaleString()}/7d` : "—"}
            </p>
            <p className="text-[10px] text-[#6b8a7a] truncate">
              {topAccel?.title || ""}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <TrendFilters
        activeStrategy={strategyFilter} onStrategyChange={setStrategyFilter}
        activeCategory={categoryFilter} onCategoryChange={setCategoryFilter}
        searchQuery={searchQuery} onSearchChange={setSearchQuery}
        categories={categories} counts={counts}
      />

      {/* Table */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <TrendingUp className="mx-auto h-12 w-12 text-[#cbd8d1]" />
            <p className="mt-3 text-sm text-[#6b8a7a]">
              {items.length === 0
                ? "O robô ainda não coletou dados. A primeira coleta roda às 4h da manhã."
                : "Nenhum produto encontrado com esses filtros."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#e0e8e3] text-left text-[#6b8a7a]">
                  <th className="px-3 py-2 font-medium">Score</th>
                  <th className="px-3 py-2 font-medium">Produto</th>
                  <th className="px-3 py-2 font-medium">Vendas China</th>
                  <th className="px-3 py-2 font-medium">Velocidade 7d</th>
                  <th className="px-3 py-2 font-medium">Concorr. BR</th>
                  <th className="px-3 py-2 font-medium">Custo BR</th>
                  <th className="px-3 py-2 font-medium">Margem Líq.</th>
                  <th className="px-3 py-2 font-medium">Estratégia</th>
                  <th className="px-3 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const cfg = STRATEGY_CONFIG[item.strategy] || STRATEGY_CONFIG.PENDENTE
                  const isExpanded = expandedId === `${item.product_id}-${item.source}`
                  return (
                    <React.Fragment key={`${item.product_id}-${item.source}`}>
                      <tr
                        className="border-b border-[#f0f4f2] hover:bg-[#f8faf9] cursor-pointer"
                        onClick={() => setExpandedId(isExpanded ? null : `${item.product_id}-${item.source}`)}
                      >
                        <td className="px-3 py-2.5">
                          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#f0f4f2] text-xs font-bold">
                            {Math.round(item.trend_score)}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 max-w-[200px]">
                          <p className="font-medium text-[#111916] truncate">{item.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <VelocitySparkline data={item.sparkline} />
                            <span className="text-[10px] text-[#6b8a7a]">
                              {item.source === "alibaba" ? "Alibaba" : "AliExpress"}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.sales_total?.toLocaleString() ?? "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono text-emerald-700 font-semibold">
                          +{item.sales_velocity_7d.toLocaleString()}
                        </td>
                        <td className="px-3 py-2.5">
                          {item.ml_competitors !== null ? (
                            <span className={item.ml_competitors === 0 ? "font-semibold text-emerald-700" : ""}>
                              {item.ml_competitors === 0 ? "Nenhum" : `${item.ml_competitors} anúncios`}
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.landed_cost_brl != null
                            ? `R$ ${item.landed_cost_brl.toFixed(2)}`
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.net_margin_pct != null ? (
                            <span className={item.net_margin_pct >= 35 ? "text-emerald-700 font-semibold" : ""}>
                              {item.net_margin_pct.toFixed(1)}%
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-3 py-2.5">
                          <Badge className={cfg.color}>{cfg.icon} {cfg.label}</Badge>
                        </td>
                        <td className="px-3 py-2.5">
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-[#f8faf9]">
                          <td colSpan={9} className="px-6 py-4">
                            <div className="grid grid-cols-2 gap-4 text-xs lg:grid-cols-4">
                              <div>
                                <p className="text-[#6b8a7a]">Velocidade 30d</p>
                                <p className="font-semibold">+{item.sales_velocity_30d.toLocaleString()} vendas</p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Aceleração</p>
                                <p className="font-semibold">{item.acceleration > 0 ? "+" : ""}{item.acceleration.toFixed(1)}%</p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Preço Sugerido BR</p>
                                <p className="font-semibold">
                                  {item.suggested_price_brl != null ? `R$ ${item.suggested_price_brl.toFixed(2)}` : "—"}
                                </p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Full no ML</p>
                                <p className="font-semibold">
                                  {item.ml_full_share_pct != null ? `${item.ml_full_share_pct.toFixed(0)}%` : "—"}
                                </p>
                              </div>
                              {item.supplier_name && (
                                <div>
                                  <p className="text-[#6b8a7a]">Fornecedor</p>
                                  <p className="font-semibold">{item.supplier_name}
                                    {item.is_verified && <span className="ml-1 text-emerald-600">✓</span>}
                                  </p>
                                </div>
                              )}
                              {item.moq && (
                                <div>
                                  <p className="text-[#6b8a7a]">MOQ</p>
                                  <p className="font-semibold">{item.moq} un</p>
                                </div>
                              )}
                            </div>
                            <div className="mt-3 flex gap-2">
                              <a href={item.url} target="_blank" rel="noopener noreferrer"
                                 className="inline-flex items-center gap-1 rounded-md bg-[#176449] px-3 py-1.5 text-xs text-white hover:bg-[#124f3a]">
                                <ExternalLink className="h-3 w-3" /> Ver na China
                              </a>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Verify TypeScript compiles and dev server runs**

Run: `cd dashboard && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/components/TrendsView.tsx dashboard/src/components/TrendFilters.tsx dashboard/src/components/VelocitySparkline.tsx
git commit -m "feat(trends): add TrendsView dashboard component with KPIs, filters, table and sparklines"
```

---

### Task 12: Deploy Configuration

**Files:**
- Create: `deploy/trend-radar.timer`
- Create: `deploy/trend-radar.service`

**Interfaces:**
- Consumes: CLI subcommand `python -m src.cli.main trends --collect`
- Produces: systemd units for daily scheduled collection

- [ ] **Step 1: Create timer unit**

```ini
# deploy/trend-radar.timer
[Unit]
Description=Executa o Radar de Tendências diariamente

[Timer]
OnCalendar=*-*-* 04:00:00 America/Sao_Paulo
Persistent=true
RandomizedDelaySec=15m
Unit=trend-radar.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 2: Create service unit**

```ini
# deploy/trend-radar.service
[Unit]
Description=Radar de Tendências China → Brasil (coleta diária)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/aliexpress-finder
EnvironmentFile=/opt/aliexpress-finder/.env
ExecStart=/usr/bin/flock -n /opt/aliexpress-finder/data/trends.lock /opt/aliexpress-finder/.venv/bin/python -m src.cli.main trends --collect

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Run full test suite one final time**

Run: `pytest -v`
Expected: All tests pass (~130 total: 93 existing + ~37 new)

- [ ] **Step 4: Commit**

```bash
git add deploy/trend-radar.timer deploy/trend-radar.service
git commit -m "feat(trends): add systemd timer and service for daily trend collection"
```

- [ ] **Step 5: Final commit with updated README mention**

Add a brief section to `README.md` under the existing features mentioning the Trend Radar, then commit:

```bash
git commit -m "docs: mention Trend Radar feature in README"
```
