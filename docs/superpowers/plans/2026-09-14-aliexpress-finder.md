# AliExpress Resale Finder & Tax Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust, accurate CLI tool to search AliExpress for reselling opportunities in Brazil, filtering out scam/accessory listings, calculating landed costs under Brazilian import tax rules (Remessa Conforme + ICMS), and estimating net resale profits and ROI.

**Architecture:** Modular Python package with independent layers: financial engine (taxes and resale margins), intelligent filter pipeline (anti-trick accessory filtering, semantic keywords, reputation), search clients (immediate stealth direct scraper + TOP protocol official API connector), and a rich terminal CLI with Excel export.

**Tech Stack:** Python 3.10+, `requests`, `beautifulsoup4`, `rich`, `pandas`, `openpyxl`, `python-dotenv`, `pytest`.

**Spec:** [2026-09-14-aliexpress-finder-design.md](file:///C:/Users/iuryc/projects/aliexpress-finder/docs/superpowers/specs/2026-09-14-aliexpress-finder-design.md)

## Global Constraints

- **Python Version**: Python 3.10+ on Windows.
- **Import Rules**: Must support Remessa Conforme: 20% II for $\le$ US$ 50; 60% II with US$ 20 deduction for $>$ US$ 50; ICMS calculated "por dentro" (grossed-up base).
- **No Heavy Dependencies**: Use lightweight HTTP scraping with stealth headers rather than requiring full browser binaries unless explicitly enabled.
- **Encoding**: UTF-8 throughout.
- **Modularity**: Every module must have independent unit tests.

---

### Task 1: Project Scaffolding & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass in `src/config.py` containing:
  - `ALIEXPRESS_APP_KEY: str`
  - `ALIEXPRESS_APP_SECRET: str`
  - `DEFAULT_USD_BRL: float` (default 5.50)
  - `DEFAULT_ICMS_RATE: float` (default 0.17)
  - `DEFAULT_MARKETPLACE_FEE: float` (default 0.16)
  - `DEFAULT_TARGET_MARGIN: float` (default 0.40)
  - `MIN_STORE_RATING: float` (default 4.5)
  - `MIN_SALES_COUNT: int` (default 10)

- [ ] **Step 1: Write requirements.txt and .env.example**

Create `requirements.txt`:
```text
requests>=2.31.0
beautifulsoup4>=4.12.0
rich>=13.7.0
pandas>=2.1.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

Create `.env.example`:
```ini
ALIEXPRESS_APP_KEY=
ALIEXPRESS_APP_SECRET=
DEFAULT_USD_BRL=5.50
DEFAULT_ICMS_RATE=0.17
DEFAULT_MARKETPLACE_FEE=0.16
DEFAULT_TARGET_MARGIN=0.40
```

- [ ] **Step 2: Write failing test for Config in tests/test_config.py**

```python
import os
from src.config import Config, load_config

def test_default_config():
    cfg = Config()
    assert cfg.DEFAULT_USD_BRL > 0
    assert cfg.DEFAULT_ICMS_RATE == 0.17
    assert cfg.DEFAULT_MARKETPLACE_FEE == 0.16
    assert cfg.DEFAULT_TARGET_MARGIN == 0.40
    assert cfg.MIN_STORE_RATING == 4.5
    assert cfg.MIN_SALES_COUNT == 10

def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_USD_BRL", "6.00")
    monkeypatch.setenv("DEFAULT_ICMS_RATE", "0.20")
    cfg = load_config()
    assert cfg.DEFAULT_USD_BRL == 6.00
    assert cfg.DEFAULT_ICMS_RATE == 0.20
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_config.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 4: Implement src/config.py**

```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    ALIEXPRESS_APP_KEY: str = ""
    ALIEXPRESS_APP_SECRET: str = ""
    DEFAULT_USD_BRL: float = 5.50
    DEFAULT_ICMS_RATE: float = 0.17
    DEFAULT_MARKETPLACE_FEE: float = 0.16
    DEFAULT_TARGET_MARGIN: float = 0.40
    MIN_STORE_RATING: float = 4.5
    MIN_SALES_COUNT: int = 10

def load_config() -> Config:
    return Config(
        ALIEXPRESS_APP_KEY=os.getenv("ALIEXPRESS_APP_KEY", ""),
        ALIEXPRESS_APP_SECRET=os.getenv("ALIEXPRESS_APP_SECRET", ""),
        DEFAULT_USD_BRL=float(os.getenv("DEFAULT_USD_BRL", "5.50")),
        DEFAULT_ICMS_RATE=float(os.getenv("DEFAULT_ICMS_RATE", "0.17")),
        DEFAULT_MARKETPLACE_FEE=float(os.getenv("DEFAULT_MARKETPLACE_FEE", "0.16")),
        DEFAULT_TARGET_MARGIN=float(os.getenv("DEFAULT_TARGET_MARGIN", "0.40")),
        MIN_STORE_RATING=float(os.getenv("MIN_STORE_RATING", "4.5")),
        MIN_SALES_COUNT=int(os.getenv("MIN_SALES_COUNT", "10")),
    )
```

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest tests/test_config.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example src/__init__.py src/config.py tests/test_config.py
git commit -m "feat: add project scaffolding and configuration module"
```

---

### Task 2: Brazilian Tax Engine (Remessa Conforme + ICMS)

**Files:**
- Create: `src/finance/__init__.py`
- Create: `src/finance/taxes.py`
- Test: `tests/test_taxes.py`

**Interfaces:**
- Consumes: None (pure calculations).
- Produces:
  ```python
  @dataclass
  class TaxCalculationResult:
      customs_value_brl: float
      customs_value_usd: float
      is_under_50_usd: bool
      import_tax_brl: float
      icms_base_brl: float
      icms_tax_brl: float
      total_taxes_brl: float
      total_landed_cost_brl: float

  def calculate_import_taxes(
      product_price_brl: float,
      shipping_fee_brl: float,
      usd_brl_rate: float = 5.50,
      icms_rate: float = 0.17
  ) -> TaxCalculationResult
  ```

- [ ] **Step 1: Write failing test in tests/test_taxes.py**

```python
import pytest
from src.finance.taxes import calculate_import_taxes

def test_under_50_usd_tax():
    # R$ 100 + R$ 10 = R$ 110 customs value. At USD 5.50, $20.00 (< $50).
    # II = 20% of 110 = 22.00
    # ICMS Base = (110 + 22) / (1 - 0.17) = 132 / 0.83 = 159.036
    # ICMS = 159.036 * 0.17 = 27.036
    # Total Taxes = 22 + 27.04 = 49.04
    # Landed Cost = 110 + 49.04 = 159.04
    res = calculate_import_taxes(product_price_brl=100.0, shipping_fee_brl=10.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert res.is_under_50_usd is True
    assert pytest.approx(res.customs_value_brl, 0.01) == 110.0
    assert pytest.approx(res.import_tax_brl, 0.01) == 22.0
    assert pytest.approx(res.icms_tax_brl, 0.01) == 27.04
    assert pytest.approx(res.total_taxes_brl, 0.01) == 49.04
    assert pytest.approx(res.total_landed_cost_brl, 0.01) == 159.04

def test_over_50_usd_tax():
    # R$ 500 + R$ 50 = R$ 550 customs value. At USD 5.50, $100.00 (> $50).
    # II = (60% of 550) - (20 USD * 5.50) = 330 - 110 = 220.00
    # ICMS Base = (550 + 220) / (1 - 0.17) = 770 / 0.83 = 927.71
    # ICMS = 927.71 * 0.17 = 157.71
    # Total Taxes = 220 + 157.71 = 377.71
    # Landed Cost = 550 + 377.71 = 927.71
    res = calculate_import_taxes(product_price_brl=500.0, shipping_fee_brl=50.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert res.is_under_50_usd is False
    assert pytest.approx(res.import_tax_brl, 0.01) == 220.0
    assert pytest.approx(res.icms_tax_brl, 0.01) == 157.71
    assert pytest.approx(res.total_taxes_brl, 0.01) == 377.71
    assert pytest.approx(res.total_landed_cost_brl, 0.01) == 927.71
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_taxes.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.finance'`

- [ ] **Step 3: Implement src/finance/taxes.py**

```python
from dataclasses import dataclass

@dataclass
class TaxCalculationResult:
    customs_value_brl: float
    customs_value_usd: float
    is_under_50_usd: bool
    import_tax_brl: float
    icms_base_brl: float
    icms_tax_brl: float
    total_taxes_brl: float
    total_landed_cost_brl: float

def calculate_import_taxes(
    product_price_brl: float,
    shipping_fee_brl: float = 0.0,
    usd_brl_rate: float = 5.50,
    icms_rate: float = 0.17
) -> TaxCalculationResult:
    """
    Calculates Brazilian import taxes according to Remessa Conforme rules:
    - Under or equal to US$ 50: 20% Import Tax (II)
    - Over US$ 50: 60% Import Tax (II) with a fixed deduction of US$ 20
    - ICMS: Calculated 'por dentro' (grossed-up base): (Customs Value + II) / (1 - ICMS) * ICMS
    """
    if usd_brl_rate <= 0:
        raise ValueError("usd_brl_rate must be greater than 0")
    if icms_rate >= 1.0 or icms_rate < 0:
        raise ValueError("icms_rate must be between 0 and 1 (exclusive of 1)")

    customs_value_brl = round(product_price_brl + shipping_fee_brl, 2)
    customs_value_usd = round(customs_value_brl / usd_brl_rate, 2)
    is_under_50_usd = customs_value_usd <= 50.00

    if is_under_50_usd:
        import_tax_brl = round(0.20 * customs_value_brl, 2)
    else:
        gross_ii = 0.60 * customs_value_brl
        deduction = 20.00 * usd_brl_rate
        import_tax_brl = round(max(0.0, gross_ii - deduction), 2)

    icms_base = (customs_value_brl + import_tax_brl) / (1.0 - icms_rate)
    icms_tax_brl = round(icms_base * icms_rate, 2)
    icms_base_brl = round(icms_base, 2)

    total_taxes_brl = round(import_tax_brl + icms_tax_brl, 2)
    total_landed_cost_brl = round(customs_value_brl + total_taxes_brl, 2)

    return TaxCalculationResult(
        customs_value_brl=customs_value_brl,
        customs_value_usd=customs_value_usd,
        is_under_50_usd=is_under_50_usd,
        import_tax_brl=import_tax_brl,
        icms_base_brl=icms_base_brl,
        icms_tax_brl=icms_tax_brl,
        total_taxes_brl=total_taxes_brl,
        total_landed_cost_brl=total_landed_cost_brl,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_taxes.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/finance/__init__.py src/finance/taxes.py tests/test_taxes.py
git commit -m "feat: implement Brazilian Remessa Conforme and ICMS tax engine"
```

---

### Task 3: Margin & Resale Profit Simulator

**Files:**
- Create: `src/finance/margins.py`
- Test: `tests/test_margins.py`

**Interfaces:**
- Consumes: `total_landed_cost_brl` from `taxes.py`.
- Produces:
  ```python
  @dataclass
  class MarginSimulationResult:
      landed_cost_brl: float
      suggested_sale_price_brl: float
      marketplace_fee_pct: float
      marketplace_fee_brl: float
      net_revenue_brl: float
      net_profit_brl: float
      net_margin_pct: float
      roi_pct: float

  def simulate_resale(
      landed_cost_brl: float,
      target_margin_pct: float = 0.40,
      marketplace_fee_pct: float = 0.16
  ) -> MarginSimulationResult
  ```

- [ ] **Step 1: Write failing test in tests/test_margins.py**

```python
import pytest
from src.finance.margins import simulate_resale

def test_simulate_resale_margin():
    # Landed Cost = R$ 100. Marketplace Fee = 16%. Target Net Margin = 40% on sale price.
    # Sale Price S must satisfy: S - (0.16 * S) - 100 = 0.40 * S
    # => S * (1 - 0.16 - 0.40) = 100 => S * 0.44 = 100 => S = 100 / 0.44 = 227.27
    # Fee = 227.27 * 0.16 = 36.36
    # Net Revenue = 227.27 - 36.36 = 190.91
    # Net Profit = 190.91 - 100 = 90.91 (= 40% of 227.27)
    # ROI = 90.91 / 100 = 90.91%
    res = simulate_resale(landed_cost_brl=100.0, target_margin_pct=0.40, marketplace_fee_pct=0.16)
    assert pytest.approx(res.suggested_sale_price_brl, 0.01) == 227.27
    assert pytest.approx(res.marketplace_fee_brl, 0.01) == 36.36
    assert pytest.approx(res.net_profit_brl, 0.01) == 90.91
    assert pytest.approx(res.net_margin_pct, 0.01) == 0.40
    assert pytest.approx(res.roi_pct, 0.01) == 90.91
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_margins.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.finance.margins'`

- [ ] **Step 3: Implement src/finance/margins.py**

```python
from dataclasses import dataclass

@dataclass
class MarginSimulationResult:
    landed_cost_brl: float
    suggested_sale_price_brl: float
    marketplace_fee_pct: float
    marketplace_fee_brl: float
    net_revenue_brl: float
    net_profit_brl: float
    net_margin_pct: float
    roi_pct: float

def simulate_resale(
    landed_cost_brl: float,
    target_margin_pct: float = 0.40,
    marketplace_fee_pct: float = 0.16
) -> MarginSimulationResult:
    """
    Simulates resale price, fees, net profit and ROI.
    Formula:
    Sale Price = Landed Cost / (1 - marketplace_fee_pct - target_margin_pct)
    """
    denominator = 1.0 - marketplace_fee_pct - target_margin_pct
    if denominator <= 0:
        raise ValueError("Sum of marketplace fee and target margin must be less than 100%")

    suggested_sale_price = round(landed_cost_brl / denominator, 2)
    marketplace_fee = round(suggested_sale_price * marketplace_fee_pct, 2)
    net_revenue = round(suggested_sale_price - marketplace_fee, 2)
    net_profit = round(net_revenue - landed_cost_brl, 2)
    roi_pct = round((net_profit / landed_cost_brl) * 100.0, 2) if landed_cost_brl > 0 else 0.0
    actual_margin_pct = round(net_profit / suggested_sale_price, 2) if suggested_sale_price > 0 else 0.0

    return MarginSimulationResult(
        landed_cost_brl=landed_cost_brl,
        suggested_sale_price_brl=suggested_sale_price,
        marketplace_fee_pct=marketplace_fee_pct,
        marketplace_fee_brl=marketplace_fee,
        net_revenue_brl=net_revenue,
        net_profit_brl=net_profit,
        net_margin_pct=actual_margin_pct,
        roi_pct=roi_pct,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_margins.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/finance/margins.py tests/test_margins.py
git commit -m "feat: implement margin and resale profit simulator"
```

---

### Task 4: Intelligent Filter Pipeline (Anti-Trick, Semantic, Reputation)

**Files:**
- Create: `src/filters/__init__.py`
- Create: `src/filters/anti_trick.py`
- Create: `src/filters/semantic.py`
- Create: `src/filters/reputation.py`
- Create: `src/filters/pipeline.py`
- Test: `tests/test_filters.py`

**Interfaces:**
- Consumes: Product item dictionary.
- Produces: `FilterPipeline.filter_products(items: list[dict], search_query: str, include_terms: list[str], exclude_terms: list[str]) -> list[dict]`

- [ ] **Step 1: Write failing tests in tests/test_filters.py**

```python
from src.filters.anti_trick import is_accessory_trick
from src.filters.semantic import matches_semantic_criteria
from src.filters.reputation import satisfies_reputation
from src.filters.pipeline import FilterPipeline

def test_anti_trick_accessory_detection():
    # Should flag accessory items disguised as watch listings
    assert is_accessory_trick("Silicone strap for watch band 20mm", main_query="relogio automatico") is True
    assert is_accessory_trick("Empty watch box display case", main_query="relogio") is True
    assert is_accessory_trick("Pagani Design Automatic Watch NH35", main_query="relogio automatico") is False

def test_semantic_terms_inclusion_and_exclusion():
    item_title = "Tandorio 39mm Automatic Diver Watch Sapphire Glass Sterile Dial"
    # Includes required terms
    assert matches_semantic_criteria(item_title, include_terms=["safira", "sterile"], exclude_terms=["quartz"]) is True
    
    # Excluded term present
    quartz_item = "Luxury Quartz Watch Sapphire Glass"
    assert matches_semantic_criteria(quartz_item, include_terms=["safira"], exclude_terms=["quartz"]) is False

def test_reputation_filter():
    assert satisfies_reputation(rating=4.8, sales=150, min_rating=4.5, min_sales=10) is True
    assert satisfies_reputation(rating=4.2, sales=150, min_rating=4.5, min_sales=10) is False
    assert satisfies_reputation(rating=4.9, sales=2, min_rating=4.5, min_sales=10) is False

def test_filter_pipeline():
    pipeline = FilterPipeline()
    items = [
        {"title": "Watch Strap 20mm", "price": 15.0, "rating": 4.9, "sales": 100},
        {"title": "Quartz Watch Safira", "price": 80.0, "rating": 4.7, "sales": 50},
        {"title": "Relógio Automático Vidro Safira Sem Logo", "price": 250.0, "rating": 4.8, "sales": 35},
        {"title": "Relógio Automático Safira Sem Logo Loja Ruim", "price": 240.0, "rating": 3.9, "sales": 1},
    ]
    filtered = pipeline.filter_products(
        items=items,
        search_query="relogio automatico",
        include_terms=["safira", "sem logo"],
        exclude_terms=["quartz", "pulseira"]
    )
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Relógio Automático Vidro Safira Sem Logo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_filters.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.filters'`

- [ ] **Step 3: Implement src/filters/anti_trick.py**

```python
import re

ACCESSORY_KEYWORDS = [
    r"\bpulseira\b", r"\bstrap\b", r"\bband\b", r"\bbracelet\b",
    r"\bcaixa vazia\b", r"\bbox only\b", r"\bcase only\b", r"\bferramenta\b",
    r"\btool\b", r"\bpeça de reposição\b", r"\bspare part\b", r"\bfecho\b", r"\bbuckle\b"
]

def is_accessory_trick(title: str, main_query: str) -> bool:
    """
    Checks if a listing is actually an accessory (strap, case, tool)
    when the user is searching for a main item (e.g. watch).
    """
    title_lower = title.lower()
    query_lower = main_query.lower()

    # If the user is specifically looking for straps or parts, don't filter them out
    if any(k in query_lower for k in ["pulseira", "strap", "band", "caixa", "ferramenta"]):
        return False

    for pattern in ACCESSORY_KEYWORDS:
        if re.search(pattern, title_lower):
            # Check if title doesn't clearly say it includes the complete watch
            if not any(w in title_lower for w in ["watch", "relógio", "relogio"]):
                return True
            # Even if it says watch, if it says "strap for watch" or "case for watch"
            if re.search(rf"{pattern}\s+(for|para|de)\s+", title_lower):
                return True

    return False
```

- [ ] **Step 4: Implement src/filters/semantic.py**

```python
import unicodedata

SYNONYMS = {
    "safira": ["safira", "sapphire", "safir"],
    "sem logo": ["sem logo", "sem logotipo", "sterile", "sterile dial", "no logo", "unbranded"],
    "automatico": ["automatico", "automático", "automatic", "nh35", "nh36", "miyota"],
    "aço": ["aco", "aço", "stainless steel", "steel", "316l"],
}

def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def matches_semantic_criteria(title: str, include_terms: list[str], exclude_terms: list[str]) -> bool:
    norm_title = normalize_text(title)

    # Exclude terms check
    for term in exclude_terms:
        norm_term = normalize_text(term.strip())
        if not norm_term:
            continue
        syns = SYNONYMS.get(norm_term, [norm_term])
        if any(normalize_text(s) in norm_title for s in syns):
            return False

    # Include terms check (all must match)
    for term in include_terms:
        norm_term = normalize_text(term.strip())
        if not norm_term:
            continue
        syns = SYNONYMS.get(norm_term, [norm_term])
        if not any(normalize_text(s) in norm_title for s in syns):
            return False

    return True
```

- [ ] **Step 5: Implement src/filters/reputation.py and pipeline.py**

Create `src/filters/reputation.py`:
```python
def satisfies_reputation(rating: float, sales: int, min_rating: float = 4.5, min_sales: int = 10) -> bool:
    # If rating is 0.0 (no reviews yet), fail reputation check for reselling safety
    if rating < min_rating:
        return False
    if sales < min_sales:
        return False
    return True
```

Create `src/filters/pipeline.py`:
```python
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
```

- [ ] **Step 6: Run tests and verify they pass**

Run: `pytest tests/test_filters.py`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/filters/ tests/test_filters.py
git commit -m "feat: implement anti-trick, semantic, and reputation filter pipeline"
```

---

### Task 5: AliExpress Search Client (Stealth Direct Scraper)

**Files:**
- Create: `src/clients/__init__.py`
- Create: `src/clients/base_client.py`
- Create: `src/clients/direct_scraper.py`
- Test: `tests/test_direct_scraper.py`

**Interfaces:**
- Consumes: `Config`
- Produces: `DirectAliExpressClient.search(query: str, max_items: int = 30) -> list[dict]`

- [ ] **Step 1: Write test for HTML parser in tests/test_direct_scraper.py**

```python
from src.clients.direct_scraper import parse_aliexpress_html_items

MOCK_HTML = """
<div class="search-item-card" data-product-id="1005001234">
    <a class="item-link" href="//www.aliexpress.com/item/1005001234.html"></a>
    <h1 class="multi--titleText--nXeOvyr">Pagani Design 40mm Sapphire NH35 Automatic Watch</h1>
    <div class="multi--price-sale--2D-y04C">R$ 190,50</div>
    <span class="multi--trade--Ktbl2jB">150 vendidos</span>
    <span class="multi--evaluation--1a2b3c">4.8</span>
</div>
"""

def test_parse_aliexpress_items():
    items = parse_aliexpress_html_items(MOCK_HTML)
    assert len(items) == 1
    assert items[0]["id"] == "1005001234"
    assert "Pagani Design" in items[0]["title"]
    assert items[0]["price"] == 190.50
    assert items[0]["sales"] == 150
    assert items[0]["rating"] == 4.8
    assert "aliexpress.com/item/1005001234.html" in items[0]["url"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_direct_scraper.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.clients'`

- [ ] **Step 3: Implement src/clients/base_client.py & direct_scraper.py**

Create `src/clients/base_client.py`:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSearchClient(ABC):
    @abstractmethod
    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        pass
```

Create `src/clients/direct_scraper.py`:
```python
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from src.clients.base_client import BaseSearchClient

def parse_price(price_str: str) -> float:
    # Extracts numbers from formats like "R$ 190,50" or "US $35.00"
    clean = re.sub(r"[^\d,\.]", "", price_str)
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0

def parse_sales(sales_str: str) -> int:
    m = re.search(r"(\d+[\.\,]?\d*)[kK]?", sales_str)
    if not m:
        return 0
    val_str = m.group(1).replace(",", ".")
    val = float(val_str)
    if "k" in sales_str.lower():
        val *= 1000
    return int(val)

def parse_aliexpress_html_items(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # Handle standard AliExpress card selectors and fallback containers
    cards = soup.find_all("div", class_=lambda c: c and "search-item-card" in c)
    if not cards:
        cards = soup.find_all("div", class_=lambda c: c and ("list--gallery--" in c or "multi--content--" in c))

    for card in cards:
        product_id = card.get("data-product-id") or ""
        link_el = card.find("a", href=True)
        url = link_el["href"] if link_el else ""
        if url.startswith("//"):
            url = "https:" + url

        if not product_id and url:
            m = re.search(r"/item/(\d+)\.html", url)
            if m:
                product_id = m.group(1)

        title_el = card.find(class_=lambda c: c and ("title" in c.lower()))
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = card.find(class_=lambda c: c and ("price" in c.lower()))
        price = parse_price(price_el.get_text(strip=True)) if price_el else 0.0

        trade_el = card.find(class_=lambda c: c and ("trade" in c.lower() or "sold" in c.lower()))
        sales = parse_sales(trade_el.get_text(strip=True)) if trade_el else 0

        eval_el = card.find(class_=lambda c: c and ("evaluation" in c.lower() or "rating" in c.lower() or "star" in c.lower()))
        try:
            rating = float(re.search(r"\d+\.\d+", eval_el.get_text(strip=True)).group(0)) if eval_el else 0.0
        except (AttributeError, ValueError):
            rating = 0.0

        if title and price > 0:
            items.append({
                "id": product_id,
                "title": title,
                "price": price,
                "shipping": 0.0,  # Default free shipping or fetched via product detail
                "sales": sales,
                "rating": rating,
                "url": url,
            })

    return items

class DirectAliExpressClient(BaseSearchClient):
    """
    Lightweight stealth HTTP scraper simulating Brazilian locale and BRL currency.
    """
    SEARCH_URL = "https://pt.aliexpress.com/w/wholesale-{query}.html"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        # Cookies to set country BR, currency BRL
        self.session.cookies.set("aep_usuc_f", "site=bra&c_tp=BRL&region=BR&b_locale=pt_BR", domain=".aliexpress.com")

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        clean_query = query.replace(" ", "-")
        url = self.SEARCH_URL.format(query=urllib.parse.quote(clean_query))
        params = {
            "SortType": "price_asc",  # Sort by cheapest first
            "g": "y",
            "page": 1,
        }
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            items = parse_aliexpress_html_items(response.text)
            return items[:max_items]
        except Exception:
            return []
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_direct_scraper.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clients/ tests/test_direct_scraper.py
git commit -m "feat: implement stealth direct AliExpress search scraper"
```

---

### Task 6: Official API Client Skeleton (TOP Protocol / HMAC-SHA256)

**Files:**
- Create: `src/clients/official_api.py`
- Test: `tests/test_official_api.py`

**Interfaces:**
- Consumes: `app_key`, `app_secret` from `Config`.
- Produces: `OfficialAliExpressClient.generate_sign(params: dict, secret: str) -> str` and `search(...)` method.

- [ ] **Step 1: Write test for TOP signature generator in tests/test_official_api.py**

```python
from src.clients.official_api import generate_top_signature

def test_generate_top_signature():
    secret = "my_secret_key"
    params = {
        "app_key": "12345678",
        "method": "aliexpress.affiliate.product.query",
        "timestamp": "2026-09-14 00:00:00",
        "format": "json",
        "v": "2.0",
        "sign_method": "sha256",
        "keywords": "watch",
    }
    sign = generate_top_signature(params, secret)
    assert isinstance(sign, str)
    assert len(sign) == 64  # SHA256 hex string length
    # Check deterministic output
    assert sign == generate_top_signature(params, secret)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_official_api.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.clients.official_api'`

- [ ] **Step 3: Implement src/clients/official_api.py**

```python
import hmac
import hashlib
from typing import Dict, Any, List
from src.clients.base_client import BaseSearchClient

def generate_top_signature(params: Dict[str, Any], app_secret: str) -> str:
    """
    Computes TOP Protocol HMAC-SHA256 signature:
    1. Sort parameters alphabetically by key.
    2. Concatenate key + value.
    3. Sign using HMAC-SHA256 with app_secret as the key.
    4. Return uppercase hex string.
    """
    sorted_keys = sorted(params.keys())
    query_str = "".join(f"{k}{params[k]}" for k in sorted_keys if k != "sign")
    signature = hmac.new(
        app_secret.encode("utf-8"),
        query_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

class OfficialAliExpressClient(BaseSearchClient):
    GATEWAY_URL = "https://api-sg.aliexpress.com/rest"

    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        # Official endpoint implementation ready to query api-sg once approved
        return []
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `pytest tests/test_official_api.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/clients/official_api.py tests/test_official_api.py
git commit -m "feat: implement official TOP Protocol signature and client skeleton"
```

---

### Task 7: CLI Interface, Terminal Formatter, and Exporter

**Files:**
- Create: `src/cli/__init__.py`
- Create: `src/cli/formatters.py`
- Create: `src/cli/exporter.py`
- Create: `src/cli/main.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Results from search client, filter pipeline, tax engine, and margin simulator.
- Produces: Rich terminal table rendering and Excel export.

- [ ] **Step 1: Write test for exporter in tests/test_cli.py**

```python
import os
import pandas as pd
from src.cli.exporter import export_to_excel

def test_export_to_excel(tmp_path):
    out_file = str(tmp_path / "test_opportunities.xlsx")
    records = [
        {
            "Produto": "Pagani Design Sapphire",
            "Preço Ali (R$)": 190.0,
            "Impostos BR (R$)": 85.0,
            "Custo Final (R$)": 275.0,
            "Sugestão Venda (R$)": 450.0,
            "Lucro Líquido (R$)": 103.0,
            "ROI (%)": 37.45,
            "Link": "https://aliexpress.com/item/1.html"
        }
    ]
    path = export_to_excel(records, out_file)
    assert os.path.exists(path)
    df = pd.read_excel(path)
    assert len(df) == 1
    assert df.iloc[0]["Produto"] == "Pagani Design Sapphire"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.cli'`

- [ ] **Step 3: Implement src/cli/formatters.py and exporter.py**

Create `src/cli/exporter.py`:
```python
import pandas as pd
from typing import List, Dict, Any

def export_to_excel(records: List[Dict[str, Any]], filepath: str = "oportunidades.xlsx") -> str:
    df = pd.DataFrame(records)
    df.to_excel(filepath, index=False, engine="openpyxl")
    return filepath
```

Create `src/cli/formatters.py`:
```python
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

def render_results_table(records: List[Dict[str, Any]]):
    console = Console()
    table = Table(title="💎 Melhores Oportunidades Encontradas no AliExpress (Custo Brasil & Margem)", show_header=True, header_style="bold magenta")

    table.add_column("Produto", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Preço Ali", justify="right", style="white")
    table.add_column("Impostos", justify="right", style="yellow")
    table.add_column("Custo Final", justify="right", style="bold red")
    table.add_column("Sugestão Venda", justify="right", style="bold green")
    table.add_column("Lucro Líquido", justify="right", style="bold green")
    table.add_column("ROI", justify="right", style="bold blue")
    table.add_column("Aval.", justify="center", style="yellow")
    table.add_column("Link", style="blue")

    for r in records:
        table.add_row(
            r["Produto"][:38] + "..." if len(r["Produto"]) > 40 else r["Produto"],
            f"R$ {r['Preço Ali (R$)']:.2f}",
            f"R$ {r['Impostos BR (R$)']:.2f}",
            f"R$ {r['Custo Final (R$)']:.2f}",
            f"R$ {r['Sugestão Venda (R$)']:.2f}",
            f"R$ {r['Lucro Líquido (R$)']:.2f}",
            f"{r['ROI (%)']:.1f}%",
            f"{r.get('Avaliação', 0.0):.1f}⭐",
            f"[link={r['Link']}]Abrir[/link]"
        )

    console.print(table)
```

- [ ] **Step 4: Implement src/cli/main.py**

```python
import argparse
import sys
from src.config import load_config
from src.clients.direct_scraper import DirectAliExpressClient
from src.clients.official_api import OfficialAliExpressClient
from src.filters.pipeline import FilterPipeline
from src.finance.taxes import calculate_import_taxes
from src.finance.margins import simulate_resale
from src.cli.formatters import render_results_table
from src.cli.exporter import export_to_excel
from rich.console import Console

console = Console()

def run():
    parser = argparse.ArgumentParser(description="AliExpress Resale Opportunity Finder & Tax Calculator")
    parser.add_argument("--busca", type=str, required=True, help="Termo principal de busca (ex: 'relogio automatico')")
    parser.add_argument("--incluir", type=str, default="", help="Termos obrigatórios separados por vírgula (ex: 'safira, sem logo')")
    parser.add_argument("--excluir", type=str, default="", help="Termos proibidos separados por vírgula (ex: 'quartz, pulseira')")
    parser.add_argument("--max-custo", type=float, default=None, help="Custo final máximo em R$")
    parser.add_argument("--margem", type=float, default=40.0, help="Margem líquida desejada em porcentagem (padrão: 40%)")
    parser.add_argument("--exportar", action="store_true", help="Salva os resultados em arquivo Excel")
    args = parser.parse_args()

    cfg = load_config()
    console.print(f"[bold green]🔎 Buscando no AliExpress por:[/bold green] '{args.busca}'...")

    # Choose client: official if keys are present, otherwise direct scraper
    client = OfficialAliExpressClient(cfg.ALIEXPRESS_APP_KEY, cfg.ALIEXPRESS_APP_SECRET)
    if not client.is_configured():
        client = DirectAliExpressClient()

    raw_items = client.search(args.busca, max_items=50)
    if not raw_items:
        console.print("[yellow]Nenhum produto retornado na busca preliminar ou limite atingido.[/yellow]")
        sys.exit(0)

    # Filter pipeline
    include_terms = [t.strip() for t in args.incluir.split(",") if t.strip()]
    exclude_terms = [t.strip() for t in args.excluir.split(",") if t.strip()]

    pipeline = FilterPipeline(min_rating=cfg.MIN_STORE_RATING, min_sales=cfg.MIN_SALES_COUNT)
    filtered_items = pipeline.filter_products(raw_items, args.busca, include_terms, exclude_terms)

    records = []
    target_margin = args.margem / 100.0

    for item in filtered_items:
        tax_res = calculate_import_taxes(
            product_price_brl=item["price"],
            shipping_fee_brl=item.get("shipping", 0.0),
            usd_brl_rate=cfg.DEFAULT_USD_BRL,
            icms_rate=cfg.DEFAULT_ICMS_RATE
        )

        if args.max_custo and tax_res.total_landed_cost_brl > args.max_custo:
            continue

        margin_res = simulate_resale(
            landed_cost_brl=tax_res.total_landed_cost_brl,
            target_margin_pct=target_margin,
            marketplace_fee_pct=cfg.DEFAULT_MARKETPLACE_FEE
        )

        records.append({
            "Produto": item["title"],
            "Preço Ali (R$)": item["price"],
            "Impostos BR (R$)": tax_res.total_taxes_brl,
            "Custo Final (R$)": tax_res.total_landed_cost_brl,
            "Sugestão Venda (R$)": margin_res.suggested_sale_price_brl,
            "Lucro Líquido (R$)": margin_res.net_profit_brl,
            "ROI (%)": margin_res.roi_pct,
            "Avaliação": item.get("rating", 0.0),
            "Link": item.get("url", "")
        })

    # Sort records by lowest landed cost
    records.sort(key=lambda r: r["Custo Final (R$)"])

    if not records:
        console.print("[yellow]Nenhum produto passou em todos os critérios e filtros de segurança.[/yellow]")
        sys.exit(0)

    render_results_table(records)

    if args.exportar:
        path = export_to_excel(records, "oportunidades_aliexpress.xlsx")
        console.print(f"[bold green]📊 Planilha salva com sucesso em:[/bold green] {path}")

if __name__ == "__main__":
    run()
```

- [ ] **Step 5: Run tests and verify they pass**

Run: `pytest tests/test_cli.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/cli/ tests/test_cli.py
git commit -m "feat: implement CLI main interface, table formatters, and Excel export"
```

---

### Task 8: Full Verification & Integration Test

**Files:**
- Test: `tests/test_integration.py`
- Modify: `README.md`

- [ ] **Step 1: Write integration test covering entire flow**

```python
from src.config import Config
from src.filters.pipeline import FilterPipeline
from src.finance.taxes import calculate_import_taxes
from src.finance.margins import simulate_resale

def test_full_pipeline_integration():
    mock_items = [
        {"title": "Strap only for Diver Watch", "price": 25.0, "rating": 4.9, "sales": 100},
        {"title": "Quartz Sapphire Watch", "price": 120.0, "rating": 4.8, "sales": 80},
        {"title": "Tandorio 39mm Automatic Diver Sapphire Glass Sterile Dial", "price": 220.0, "rating": 4.8, "sales": 45},
    ]

    pipeline = FilterPipeline(min_rating=4.5, min_sales=10)
    passed = pipeline.filter_products(
        items=mock_items,
        search_query="relogio automatico",
        include_terms=["safira", "sterile"],
        exclude_terms=["quartz"]
    )
    assert len(passed) == 1
    winner = passed[0]

    taxes = calculate_import_taxes(winner["price"], shipping_fee_brl=0.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert taxes.total_landed_cost_brl > winner["price"]

    margins = simulate_resale(taxes.total_landed_cost_brl, target_margin_pct=0.40, marketplace_fee_pct=0.16)
    assert margins.net_profit_brl > 0
    assert margins.suggested_sale_price_brl > taxes.total_landed_cost_brl
```

- [ ] **Step 2: Run all tests in the project**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 3: Create README.md with clear instructions and examples**

Create `README.md` with usage documentation, command examples, and tax explanations.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py README.md
git commit -m "docs: add full integration tests and project documentation"
```
