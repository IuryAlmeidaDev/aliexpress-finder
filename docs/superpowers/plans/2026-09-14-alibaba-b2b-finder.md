# Alibaba B2B Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a dedicated B2B wholesale search engine for Alibaba.com, extracting MOQ, volume prices, factory badges (Verified, Trade Assurance), and calculating batch landed cost with Brazilian import taxes and resale profit projections.

**Architecture:** A standalone `DirectAlibabaClient` implements `BaseSearchClient`, parsing Alibaba wholesale cards. A dedicated `AlibabaFilterPipeline` filters by maximum MOQ, Verified Supplier, Trade Assurance, and semantic keywords. A wholesale financial engine computes total batch investment (RTS 60% II + ICMS "por dentro") and per-unit landed costs. The CLI integrates `--fonte alibaba`, `--max-moq`, `--verificados`, and `--trade-assurance`, rendering a specialized B2B Rich table and exporting to `oportunidades_alibaba.xlsx`.

**Tech Stack:** Python 3.10+, `curl_cffi`, `requests`, `beautifulsoup4`, `rich`, `pandas`, `openpyxl`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-14-alibaba-b2b-finder-design.md`

## Global Constraints

- Platform: Windows with UTF-8 console output.
- Zero regressions on existing AliExpress functionality (`pytest` must remain 100% passing across all 33 existing tests).
- Clean separation: `--fonte alibaba` produces `oportunidades_alibaba.xlsx` and displays B2B batch metrics.
- TDD required: write failing test, verify failure, implement minimal code, verify pass, commit.

---

### Task 1: Alibaba Search Client & MOQ Parser (`src/clients/alibaba_scraper.py`)

**Files:**
- Create: `src/clients/alibaba_scraper.py`
- Test: `tests/test_alibaba_scraper.py`

**Interfaces:**
- Produces:
  - `parse_moq(moq_str: str) -> int`: Extracts integer minimum order quantity.
  - `parse_alibaba_price(price_str: str, usd_rate: float) -> float`: Extracts lowest unit price in BRL.
  - `parse_alibaba_html_items(html: str, usd_rate: float) -> List[Dict[str, Any]]`: Parses card elements into dictionaries with keys `["id", "title", "price", "moq", "supplier_name", "is_verified", "has_trade_assurance", "years_in_business", "url"]`.
  - `DirectAlibabaClient(BaseSearchClient)`: Implements `search(query: str, max_items: int = 30) -> List[Dict[str, Any]]`.

- [ ] **Step 1: Write the failing tests in `tests/test_alibaba_scraper.py`**

```python
from src.clients.alibaba_scraper import parse_moq, parse_alibaba_price, parse_alibaba_html_items

MOCK_ALIBABA_HTML = """
<div class="organic-list-offer-outter" data-spm="offer">
    <a class="organic-gallery-title" href="//www.alibaba.com/product-detail/Custom-Kids-Digital-Watch_1600123456.html">
        Custom Kids Digital Watch Colorful Silicone LED Student Watch
    </a>
    <div class="element-offer-price">$0.85 - $1.20</div>
    <div class="element-offer-minorder">Min. order: 50 pieces</div>
    <div class="organic-gallery-offer__seller-company">Shenzhen Top Time Watch Co., Ltd.</div>
    <span class="verified-icon">Verified Supplier</span>
    <span class="trade-assurance-icon">Trade Assurance</span>
    <span class="seller-tag__years">5 yrs</span>
</div>
<div class="organic-list-offer-outter" data-spm="offer">
    <a class="organic-gallery-title" href="//www.alibaba.com/product-detail/Smart-Watch-Teen_1600999999.html">
        Smart Watch Teen Unbranded
    </a>
    <div class="element-offer-price">R$ 15,50</div>
    <div class="element-offer-minorder">100 sets</div>
    <div class="organic-gallery-offer__seller-company">Guangzhou Fashion Trading</div>
</div>
"""

def test_parse_moq():
    assert parse_moq("Min. order: 50 pieces") == 50
    assert parse_moq("100 sets") == 100
    assert parse_moq("1 piece") == 1
    assert parse_moq("MOQ: 500 pcs") == 500
    assert parse_moq("") == 1

def test_parse_alibaba_price():
    # USD conversion (usd_rate=5.50)
    assert parse_alibaba_price("$0.85 - $1.20", usd_rate=5.50) == round(0.85 * 5.50, 2)
    assert parse_alibaba_price("$2.50", usd_rate=5.50) == round(2.50 * 5.50, 2)
    # BRL direct
    assert parse_alibaba_price("R$ 15,50", usd_rate=5.50) == 15.50
    assert parse_alibaba_price("", usd_rate=5.50) == 0.0

def test_parse_alibaba_html_items():
    items = parse_alibaba_html_items(MOCK_ALIBABA_HTML, usd_rate=5.50)
    assert len(items) == 2

    first = items[0]
    assert first["id"] == "1600123456"
    assert "Custom Kids Digital Watch" in first["title"]
    assert first["price"] == round(0.85 * 5.50, 2)
    assert first["moq"] == 50
    assert first["supplier_name"] == "Shenzhen Top Time Watch Co., Ltd."
    assert first["is_verified"] is True
    assert first["has_trade_assurance"] is True
    assert first["years_in_business"] == 5
    assert "alibaba.com/product-detail/Custom-Kids-Digital-Watch_1600123456.html" in first["url"]

    second = items[1]
    assert second["moq"] == 100
    assert second["price"] == 15.50
    assert second["is_verified"] is False
    assert second["has_trade_assurance"] is False
    assert second["years_in_business"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_alibaba_scraper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.clients.alibaba_scraper'`

- [ ] **Step 3: Implement `src/clients/alibaba_scraper.py`**

```python
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from src.clients.base_client import BaseSearchClient

def parse_moq(moq_str: str) -> int:
    if not moq_str:
        return 1
    m = re.search(r"(\d+[\d\s,]*)", moq_str)
    if not m:
        return 1
    clean = re.sub(r"[^\d]", "", m.group(1))
    try:
        val = int(clean)
        return val if val > 0 else 1
    except ValueError:
        return 1

def parse_alibaba_price(price_str: str, usd_rate: float = 5.50) -> float:
    if not price_str:
        return 0.0
    clean = price_str.strip()
    is_usd = "$" in clean or "USD" in clean.upper() or "US" in clean.upper()
    if "R$" in clean:
        is_usd = False

    # Extract first price token
    m = re.search(r"(\d+(?:[.,]\d+)?)", clean)
    if not m:
        return 0.0
    num_str = m.group(1)
    if "," in num_str and "." in num_str:
        num_str = num_str.replace(".", "").replace(",", ".")
    elif "," in num_str:
        num_str = num_str.replace(",", ".")
    try:
        val = float(num_str)
        if is_usd:
            return round(val * usd_rate, 2)
        return round(val, 2)
    except ValueError:
        return 0.0

def parse_alibaba_html_items(html: str, usd_rate: float = 5.50) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    cards = soup.find_all("div", class_=lambda c: c and ("organic-list-offer" in c or "search-card-e" in c or "fy23-gallery-card" in c or "list-no-v2-outer" in c))
    if not cards:
        cards = soup.find_all("div", attrs={"data-spm": lambda s: s and "offer" in s})

    for card in cards:
        link_el = card.find("a", href=True)
        url = link_el["href"] if link_el else ""
        if url.startswith("//"):
            url = "https:" + url

        product_id = ""
        m_id = re.search(r"_(\d+)\.html", url)
        if m_id:
            product_id = m_id.group(1)

        title_el = card.find(class_=lambda c: c and ("title" in c.lower()))
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = card.find(class_=lambda c: c and ("price" in c.lower()))
        price = parse_alibaba_price(price_el.get_text(strip=True), usd_rate=usd_rate) if price_el else 0.0

        moq_el = card.find(class_=lambda c: c and ("minorder" in c.lower() or "moq" in c.lower() or "min-order" in c.lower()))
        moq = parse_moq(moq_el.get_text(strip=True)) if moq_el else 1

        company_el = card.find(class_=lambda c: c and ("company" in c.lower() or "supplier" in c.lower() or "seller" in c.lower()))
        supplier_name = company_el.get_text(strip=True) if company_el else ""

        card_text = card.get_text()
        is_verified = "verified" in card_text.lower()
        has_trade_assurance = "trade assurance" in card_text.lower()

        years = 0
        m_yrs = re.search(r"(\d+)\s*(?:yrs|anos|years)", card_text, re.IGNORECASE)
        if m_yrs:
            try:
                years = int(m_yrs.group(1))
            except ValueError:
                years = 0

        if title and price > 0:
            items.append({
                "id": product_id,
                "title": title,
                "price": price,
                "moq": moq,
                "supplier_name": supplier_name,
                "is_verified": is_verified,
                "has_trade_assurance": has_trade_assurance,
                "years_in_business": years,
                "url": url,
            })

    return items

class DirectAlibabaClient(BaseSearchClient):
    SEARCH_URL = "https://www.alibaba.com/trade/search?SearchText={query}"

    def __init__(self, timeout: int = 15, usd_rate: float = 5.50):
        self.timeout = timeout
        self.usd_rate = usd_rate
        try:
            from curl_cffi import requests as curl_requests
            self.session = curl_requests.Session(impersonate="chrome124")
        except Exception:
            self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        import time
        url = self.SEARCH_URL.format(query=urllib.parse.quote(query))
        items: List[Dict[str, Any]] = []
        page = 1
        max_pages = max(1, (max_items + 11) // 12)

        while len(items) < max_items and page <= max_pages:
            params = {"page": page}
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                page_items = parse_alibaba_html_items(response.text, usd_rate=self.usd_rate)
                if not page_items:
                    break
                seen = {it.get("id") or it.get("url") for it in items}
                for it in page_items:
                    key = it.get("id") or it.get("url")
                    if key and key not in seen:
                        seen.add(key)
                        items.append(it)
                    elif not key:
                        items.append(it)
                page += 1
                if page <= max_pages and len(items) < max_items:
                    time.sleep(1.0)
            except Exception:
                break

        return items[:max_items]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_alibaba_scraper.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/clients/alibaba_scraper.py tests/test_alibaba_scraper.py
git commit -m "feat: implement DirectAlibabaClient and MOQ/price parsing"
```

---

### Task 2: Wholesale Financial Calculations (`src/finance/wholesale.py`)

**Files:**
- Create: `src/finance/wholesale.py`
- Test: `tests/test_wholesale_finance.py`

**Interfaces:**
- Produces:
  - `calculate_wholesale_batch_costs(unit_price_brl: float, moq: int, icms_rate: float = 0.17, import_tax_rate: float = 0.60) -> WholesaleBatchResult`:
    - Computes batch FOB, Import Tax (60%), ICMS ("por dentro"), total landed cost of batch, and landed cost per unit.
  - `simulate_wholesale_resale(batch_landed_cost_brl: float, moq: int, target_margin_pct: float = 0.40, marketplace_fee_pct: float = 0.16) -> WholesaleResaleResult`:
    - Computes unit suggested retail price, projected total revenue, projected total net profit, and ROI %.

- [ ] **Step 1: Write the failing tests in `tests/test_wholesale_finance.py`**

```python
import pytest
from src.finance.wholesale import calculate_wholesale_batch_costs, simulate_wholesale_resale

def test_calculate_wholesale_batch_costs():
    # Unit price R$ 10, MOQ 50 => FOB = R$ 500
    # II 60% = R$ 300 => Base before ICMS = R$ 800
    # ICMS 17% por dentro => 800 / (1 - 0.17) * 0.17 = 963.86 * 0.17 = 163.86
    # Total batch landed cost = 800 + 163.86 = 963.86
    # Unit landed cost = 963.86 / 50 = 19.28
    res = calculate_wholesale_batch_costs(unit_price_brl=10.0, moq=50, icms_rate=0.17, import_tax_rate=0.60)
    assert res.fob_batch_brl == 500.0
    assert res.import_tax_batch_brl == 300.0
    assert round(res.icms_batch_brl, 2) == 163.86
    assert round(res.total_batch_landed_cost_brl, 2) == 963.86
    assert round(res.unit_landed_cost_brl, 2) == 19.28

def test_simulate_wholesale_resale():
    # Total batch landed cost = R$ 963.86, MOQ = 50, Unit landed cost = 19.277
    # Suggested retail price per unit with 40% margin and 16% fee:
    # 19.277 / (1 - 0.16 - 0.40) = 19.277 / 0.44 = 43.81
    # Projected batch revenue: 43.81 * 50 = 2190.57
    # Marketplace fee: 2190.57 * 0.16 = 350.49
    # Net profit: 2190.57 - 350.49 - 963.86 = 876.22
    # ROI: (876.22 / 963.86) * 100 = 90.9%
    batch_res = calculate_wholesale_batch_costs(unit_price_brl=10.0, moq=50)
    resale = simulate_wholesale_resale(
        batch_landed_cost_brl=batch_res.total_batch_landed_cost_brl,
        moq=50,
        target_margin_pct=0.40,
        marketplace_fee_pct=0.16
    )
    assert round(resale.unit_sale_price_brl, 2) == 43.81
    assert round(resale.projected_revenue_brl, 2) == 2190.57
    assert round(resale.projected_net_profit_brl, 2) == 876.22
    assert round(resale.roi_pct, 1) == 90.9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_wholesale_finance.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.finance.wholesale'`

- [ ] **Step 3: Implement `src/finance/wholesale.py`**

```python
from dataclasses import dataclass

@dataclass
class WholesaleBatchResult:
    fob_batch_brl: float
    import_tax_batch_brl: float
    icms_batch_brl: float
    total_batch_landed_cost_brl: float
    unit_landed_cost_brl: float

@dataclass
class WholesaleResaleResult:
    unit_sale_price_brl: float
    projected_revenue_brl: float
    projected_net_profit_brl: float
    roi_pct: float

def calculate_wholesale_batch_costs(
    unit_price_brl: float,
    moq: int,
    icms_rate: float = 0.17,
    import_tax_rate: float = 0.60
) -> WholesaleBatchResult:
    if moq < 1:
        moq = 1
    fob_batch = unit_price_brl * moq
    import_tax = fob_batch * import_tax_rate

    # ICMS "por dentro": Base = (fob + II) / (1 - icms_rate)
    grossed_base = (fob_batch + import_tax) / (1.0 - icms_rate)
    icms = grossed_base * icms_rate

    total_batch_landed_cost = fob_batch + import_tax + icms
    unit_landed_cost = total_batch_landed_cost / moq

    return WholesaleBatchResult(
        fob_batch_brl=round(fob_batch, 2),
        import_tax_batch_brl=round(import_tax, 2),
        icms_batch_brl=round(icms, 2),
        total_batch_landed_cost_brl=round(total_batch_landed_cost, 2),
        unit_landed_cost_brl=round(unit_landed_cost, 2),
    )

def simulate_wholesale_resale(
    batch_landed_cost_brl: float,
    moq: int,
    target_margin_pct: float = 0.40,
    marketplace_fee_pct: float = 0.16
) -> WholesaleResaleResult:
    if moq < 1:
        moq = 1
    if target_margin_pct + marketplace_fee_pct >= 1.0:
        raise ValueError("Sum of margin and marketplace fee must be strictly less than 1.0 (100%)")

    unit_landed_cost = batch_landed_cost_brl / moq
    denominator = 1.0 - marketplace_fee_pct - target_margin_pct
    unit_sale_price = unit_landed_cost / denominator

    projected_revenue = unit_sale_price * moq
    fee_total = projected_revenue * marketplace_fee_pct
    projected_net_profit = projected_revenue - fee_total - batch_landed_cost_brl
    roi_pct = (projected_net_profit / batch_landed_cost_brl) * 100.0 if batch_landed_cost_brl > 0 else 0.0

    return WholesaleResaleResult(
        unit_sale_price_brl=round(unit_sale_price, 2),
        projected_revenue_brl=round(projected_revenue, 2),
        projected_net_profit_brl=round(projected_net_profit, 2),
        roi_pct=round(roi_pct, 1),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_wholesale_finance.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/finance/wholesale.py tests/test_wholesale_finance.py
git commit -m "feat: implement wholesale batch taxation and margin simulator"
```

---

### Task 3: B2B Filter Pipeline (`src/filters/alibaba_pipeline.py`)

**Files:**
- Create: `src/filters/alibaba_pipeline.py`
- Test: `tests/test_alibaba_filters.py`

**Interfaces:**
- Produces:
  - `AlibabaFilterPipeline(max_moq: Optional[int], only_verified: bool, only_trade_assurance: bool)`:
    - Implements `filter_products(items: List[Dict[str, Any]], search_query: str, include_terms: List[str], exclude_terms: List[str]) -> List[Dict[str, Any]]`.

- [ ] **Step 1: Write the failing tests in `tests/test_alibaba_filters.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_alibaba_filters.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.filters.alibaba_pipeline'`

- [ ] **Step 3: Implement `src/filters/alibaba_pipeline.py`**

```python
from typing import List, Dict, Any, Optional
from src.filters.semantic import matches_semantic_criteria

class AlibabaFilterPipeline:
    def __init__(
        self,
        max_moq: Optional[int] = None,
        only_verified: bool = False,
        only_trade_assurance: bool = False
    ):
        self.max_moq = max_moq
        self.only_verified = only_verified
        self.only_trade_assurance = only_trade_assurance

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
            moq = int(item.get("moq") or 1)
            is_verified = bool(item.get("is_verified"))
            has_trade_assurance = bool(item.get("has_trade_assurance"))

            if self.max_moq is not None and moq > self.max_moq:
                continue

            if self.only_verified and not is_verified:
                continue

            if self.only_trade_assurance and not has_trade_assurance:
                continue

            if not matches_semantic_criteria(title, include_terms, exclude_terms):
                continue

            passed.append(item)

        return passed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_alibaba_filters.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/filters/alibaba_pipeline.py tests/test_alibaba_filters.py
git commit -m "feat: implement AlibabaFilterPipeline with MOQ and supplier badge filters"
```

---

### Task 4: CLI Flags, Formatter & Exporter for Alibaba (`src/cli/`)

**Files:**
- Modify: `src/cli/formatters.py`
- Modify: `src/cli/main.py`
- Modify: `src/cli/exporter.py`
- Test: `tests/test_alibaba_cli.py`

**Interfaces:**
- `src/cli/formatters.py`: adds `render_alibaba_table(records: List[Dict[str, Any]])`
- `src/cli/main.py`: adds `--fonte` (`ali`|`alibaba`), `--max-moq`, `--verificados`, `--trade-assurance`

- [ ] **Step 1: Write the failing tests in `tests/test_alibaba_cli.py`**

```python
import sys
from unittest.mock import patch
from src.cli.main import run

MOCK_ALIBABA_ITEMS = [
    {
        "id": "1",
        "title": "Kids Watch Silicone LED",
        "price": 6.00,
        "moq": 50,
        "supplier_name": "Shenzhen Factory Ltd",
        "is_verified": True,
        "has_trade_assurance": True,
        "years_in_business": 4,
        "url": "https://alibaba.com/product/1.html"
    }
]

def test_cli_alibaba_run_success_with_export(monkeypatch, tmp_path):
    export_file = str(tmp_path / "oportunidades_alibaba.xlsx")
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio infantil", "--max-moq", "100", "--exportar"
    ])
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=MOCK_ALIBABA_ITEMS), \
         patch("src.cli.main.export_to_excel", return_value=export_file) as mock_export:
        run()
        assert mock_export.called
        assert "oportunidades_alibaba.xlsx" in mock_export.call_args[0][1]

def test_cli_alibaba_filters_moq_out(monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio", "--max-moq", "10"
    ])
    # Product requires MOQ 50, so with --max-moq 10 it should be filtered out
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=MOCK_ALIBABA_ITEMS):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_alibaba_cli.py -v`
Expected: FAIL (unrecognized arguments or missing table renderer)

- [ ] **Step 3: Update `src/cli/formatters.py` and `src/cli/main.py`**

In `src/cli/formatters.py`, add `render_alibaba_table`:
```python
def render_alibaba_table(records: List[Dict[str, Any]]):
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    console = Console()
    table = Table(
        title="🏭 Oportunidades Atacado Alibaba.com (Fábrica & Custo de Lote)",
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Produto / Fornecedor", style="white", overflow="fold", max_width=35)
    table.add_column("MOQ", justify="center", style="bold yellow")
    table.add_column("Preço Unit. (R$)", justify="right", style="cyan")
    table.add_column("Custo Unit. Final", justify="right", style="magenta")
    table.add_column("Lote Total (R$)", justify="right", style="bold red")
    table.add_column("Sugestão Venda Un.", justify="right", style="green")
    table.add_column("Lucro Lote (R$)", justify="right", style="bold green")
    table.add_column("ROI (%)", justify="right", style="bold")
    table.add_column("Selos", justify="center")
    table.add_column("Link", justify="center")

    for r in records:
        url = r.get("Link", "")
        link_str = f"[link={url}]Abrir[/link]" if url else "-"
        badges = []
        if r.get("Verified"):
            badges.append("🛡️Verif")
        if r.get("Trade Assurance"):
            badges.append("🤝TA")
        if r.get("Anos"):
            badges.append(f"{r['Anos']}a")
        badges_str = " ".join(badges) if badges else "-"

        table.add_row(
            f"{r['Produto']}\n[dim]{r.get('Fornecedor', '')}[/dim]",
            f"{r['MOQ']} un",
            f"R$ {r['Preço Unit. (R$)']:.2f}",
            f"R$ {r['Custo Unit. Final (R$)']:.2f}",
            f"R$ {r['Investimento Lote (R$)']:.2f}",
            f"R$ {r['Sugestão Venda (R$)']:.2f}",
            f"R$ {r['Lucro Líquido Lote (R$)']:.2f}",
            f"{r['ROI (%)']:.1f}%",
            badges_str,
            link_str
        )

    console.print(table)
```

In `src/cli/main.py`, parse `--fonte` (default `ali`), `--max-moq`, `--verificados`, `--trade-assurance`.
When `--fonte alibaba`:
- Use `DirectAlibabaClient`.
- Use `AlibabaFilterPipeline`.
- Calculate costs with `calculate_wholesale_batch_costs` and `simulate_wholesale_resale`.
- Render with `render_alibaba_table`.
- Export with `export_to_excel(records, "oportunidades_alibaba.xlsx")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_alibaba_cli.py -v`
Expected: 2 passed

- [ ] **Step 5: Run full test suite to ensure no regressions**

Run: `pytest -v`
Expected: 42 passed (33 existing + 9 new)

- [ ] **Step 6: Commit**

```bash
git add src/cli/formatters.py src/cli/main.py tests/test_alibaba_cli.py
git commit -m "feat: add Alibaba CLI options, table formatter, and Excel export"
```

---

### Task 5: Integration Testing & Documentation (`tests/test_alibaba_integration.py` & `README.md`)

**Files:**
- Create: `tests/test_alibaba_integration.py`
- Modify: `README.md`

- [ ] **Step 1: Write integration test covering full Alibaba flow**

```python
from src.filters.alibaba_pipeline import AlibabaFilterPipeline
from src.finance.wholesale import calculate_wholesale_batch_costs, simulate_wholesale_resale
from src.cli.exporter import export_to_excel

def test_full_alibaba_pipeline_integration(tmp_path):
    raw_items = [
        {"title": "Custom Kids LED Watch Silicone", "price": 5.0, "moq": 50, "is_verified": True, "has_trade_assurance": True, "years_in_business": 3, "supplier_name": "Tech Co", "url": "https://ali/1"},
        {"title": "Expensive Gold Watch", "price": 50.0, "moq": 500, "is_verified": False, "has_trade_assurance": False, "years_in_business": 1, "supplier_name": "Gold Co", "url": "https://ali/2"},
    ]

    pipeline = AlibabaFilterPipeline(max_moq=100, only_verified=True, only_trade_assurance=True)
    filtered = pipeline.filter_products(raw_items, search_query="watch")
    assert len(filtered) == 1

    item = filtered[0]
    costs = calculate_wholesale_batch_costs(unit_price_brl=item["price"], moq=item["moq"])
    resale = simulate_wholesale_resale(batch_landed_cost_brl=costs.total_batch_landed_cost_brl, moq=item["moq"])

    record = [{
        "Produto": item["title"],
        "Fornecedor": item["supplier_name"],
        "MOQ": item["moq"],
        "Preço Unit. (R$)": item["price"],
        "Custo Unit. Final (R$)": costs.unit_landed_cost_brl,
        "Investimento Lote (R$)": costs.total_batch_landed_cost_brl,
        "Sugestão Venda (R$)": resale.unit_sale_price_brl,
        "Lucro Líquido Lote (R$)": resale.projected_net_profit_brl,
        "ROI (%)": resale.roi_pct,
        "Link": item["url"]
    }]

    out = export_to_excel(record, str(tmp_path / "oportunidades_alibaba.xlsx"))
    assert out.endswith("oportunidades_alibaba.xlsx")
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_alibaba_integration.py -v`
Expected: 1 passed

- [ ] **Step 3: Update `README.md` with Alibaba CLI commands and B2B guide**

Add clear Portuguese documentation and examples for:
```powershell
python -m src.cli.main --fonte alibaba --busca "relogio infantil" --max-moq 50 --verificados --trade-assurance --exportar
```

- [ ] **Step 4: Run full test suite**

Run: `pytest -v`
Expected: 43 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_alibaba_integration.py README.md
git commit -m "docs: document Alibaba B2B search and add end-to-end integration test"
```
