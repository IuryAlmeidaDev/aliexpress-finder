# Plano de Implementação: Motor de Inteligência de Concorrência e Benchmarking

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implementar o subsistema de inteligência de concorrência e benchmarking de mercado no `aliexpress-finder`, permitindo dissecar anúncios (Mercado Livre e lojas virtuais em geral), mapear concorrentes diretos, analisar brechas de kits/preços e conectar com fornecedores da China.

**Architecture:** Arquitetura orientada a pipelines modulares: Extratores polimórficos (`MercadoLivreExtractor`, `UniversalWebExtractor`) transformam URLs em `TargetProduct`. O `CompetitorRadar` descobre competidores diretos. O `BenchmarkingEngine` calcula métricas e custos-alvo na China, alimentando o `MarketDossier` que é renderizado em tabelas `rich` e exportado em Markdown e Excel.

**Tech Stack:** Python 3.10+, BeautifulSoup4, Requests / Curl-cffi, Pydantic/Dataclasses, Pandas, Openpyxl, Rich, Pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-competitor-intelligence-design.md`

## Global Constraints
- Manter 100% de compatibilidade com os testes existentes de `src.finance` e `src.filters`.
- Todos os scrapers devem ter tratamento gracioso de falha (timeout e erros de conexão não derrubam a aplicação).
- Princípios de TDD: cada funcionalidade deve ter testes unitários com fixtures mockadas antes do código de produção.
- Sem dependência de chaves de API pagas para busca e extração.

---

### Task 1: Modelos de Dados (`src/competitors/models.py`)

**Files:**
- Create: `src/competitors/__init__.py`
- Create: `src/competitors/models.py`
- Test: `tests/test_competitor_models.py`

**Interfaces:**
- Produces:
  - `TargetProduct(title: str, url: str | None, reference_price_brl: float, clean_query: str, category: str, specs: dict[str, str], kit_items: list[str])`
  - `CompetitorProduct(title: str, url: str, store_name: str, platform: str, price_brl: float, original_price_brl: float | None, shipping_type: str, rating: float | None, reviews_count: int | None, sales_volume: str | None, kit_items: list[str], differentials: list[str])`
  - `MarketDossier(...)`

- [x] **Step 1: Escrever teste que falha para criação e validação dos modelos**
```python
def test_target_product_creation():
    from src.competitors.models import TargetProduct
    p = TargetProduct(
        title="Relógio Automático Safira",
        url="https://exemplo.com/relogio",
        reference_price_brl=250.0,
        clean_query="relogio automatico safira",
        specs={"vidro": "safira"},
        kit_items=["estojo"]
    )
    assert p.reference_price_brl == 250.0
    assert "estojo" in p.kit_items
```

- [x] **Step 2: Executar teste e verificar que falha**
Run: `pytest tests/test_competitor_models.py`
Expected: FAIL (módulo não encontrado)

- [x] **Step 3: Implementar `src/competitors/models.py`**
Implementar dataclasses tipadas para `TargetProduct`, `CompetitorProduct` e `MarketDossier`.

- [x] **Step 4: Executar teste e verificar que passa**
Run: `pytest tests/test_competitor_models.py`
Expected: PASS

- [x] **Step 5: Commit**
`git add src/competitors/ tests/test_competitor_models.py; git commit -m "feat(competitors): add core data models"`

---

### Task 2: Extratores Modulares (`src/competitors/extractors/`)

**Files:**
- Create: `src/competitors/extractors/__init__.py`
- Create: `src/competitors/extractors/base.py`
- Create: `src/competitors/extractors/mercadolivre.py`
- Create: `src/competitors/extractors/universal.py`
- Create: `src/competitors/extractors/router.py`
- Test: `tests/test_competitor_extractors.py`

**Interfaces:**
- Consumes: `TargetProduct` de `src.competitors.models`
- Produces:
  - `BaseExtractor.extract(url: str, html: str) -> TargetProduct`
  - `get_extractor_for_url(url: str) -> BaseExtractor`

- [x] **Step 1: Escrever testes unitários para `MercadoLivreExtractor` e `UniversalWebExtractor` com HTML fixtures**
Testar extração de título, preço, kit e especificações tanto em HTML do ML quanto em HTML padrão com JSON-LD / OpenGraph.

- [x] **Step 2: Executar teste e verificar que falha**
Run: `pytest tests/test_competitor_extractors.py`
Expected: FAIL

- [x] **Step 3: Implementar a hierarquia de extratores**
- `BaseExtractor`: contrato abstrato com `can_handle` e `extract`.
- `MercadoLivreExtractor`: parsing de OG tags, seletores e meta dados específicos do ML.
- `UniversalWebExtractor`: parsing de JSON-LD Schema.org (`Product`) e OpenGraph com fallback resiliente.
- `router.py`: função seletora que escolhe o extrator correto.

- [x] **Step 4: Executar testes e verificar que passam**
Run: `pytest tests/test_competitor_extractors.py`
Expected: PASS

- [x] **Step 5: Commit**
`git add src/competitors/extractors/ tests/test_competitor_extractors.py; git commit -m "feat(competitors): implement modular product extractors"`

---

### Task 3: Radar de Concorrência (`src/competitors/radar.py`)

**Files:**
- Create: `src/competitors/radar.py`
- Test: `tests/test_competitor_radar.py`

**Interfaces:**
- Consumes: `TargetProduct`, `CompetitorProduct`
- Produces:
  - `CompetitorRadar.find_competitors(query: str, limit: int = 5) -> list[CompetitorProduct]`

- [x] **Step 1: Escrever teste com mock HTML de busca do Mercado Livre**
Validar que a lista de concorrentes extrai preço, título, loja e badges (Full / Frete Grátis).

- [x] **Step 2: Executar teste e verificar falha**
Run: `pytest tests/test_competitor_radar.py`
Expected: FAIL

- [x] **Step 3: Implementar `CompetitorRadar`**
Implementar o cliente HTTP e parser que consulta a busca do Mercado Livre e extrai os anúncios concorrentes mais vendidos/relevantes.

- [x] **Step 4: Executar testes e verificar que passam**
Run: `pytest tests/test_competitor_radar.py`
Expected: PASS

- [x] **Step 5: Commit**
`git add src/competitors/radar.py tests/test_competitor_radar.py; git commit -m "feat(competitors): add competitor discovery radar"`

---

### Task 4: Motor de Benchmarking (`src/competitors/benchmarking.py`)

**Files:**
- Create: `src/competitors/benchmarking.py`
- Test: `tests/test_competitor_benchmarking.py`

**Interfaces:**
- Consumes: `TargetProduct`, `CompetitorProduct`, `MarketDossier`, `calculate_wholesale_batch_costs` de `src.finance.wholesale`
- Produces:
  - `BenchmarkingEngine.generate_dossier(target: TargetProduct, competitors: list[CompetitorProduct]) -> MarketDossier`

- [x] **Step 1: Escrever testes para cálculo de métricas (min, max, média, mediana, gaps de mercado e target FOB price)**

- [x] **Step 2: Executar teste e verificar falha**
Run: `pytest tests/test_competitor_benchmarking.py`
Expected: FAIL

- [x] **Step 3: Implementar `BenchmarkingEngine`**
Calcular estatísticas da concorrência, identificar kits prevalentes e calcular o teto de custo fabril na China para bater o mercado com 40% de margem líquida.

- [x] **Step 4: Executar testes e verificar que passam**
Run: `pytest tests/test_competitor_benchmarking.py`
Expected: PASS

- [x] **Step 5: Commit**
`git add src/competitors/benchmarking.py tests/test_competitor_benchmarking.py; git commit -m "feat(competitors): add benchmarking and market opportunity engine"`

---

### Task 5: Formatadores e Exportadores (`src/competitors/formatters.py`, `exporter.py`)

**Files:**
- Create: `src/competitors/formatters.py`
- Create: `src/competitors/exporter.py`
- Test: `tests/test_competitor_export.py`

**Interfaces:**
- Consumes: `MarketDossier`
- Produces:
  - `format_dossier_terminal(dossier: MarketDossier) -> Table / Console layout`
  - `export_dossier_markdown(dossier: MarketDossier, filepath: str) -> None`
  - `export_competitors_excel(dossier: MarketDossier, filepath: str) -> None`

- [x] **Step 1: Escrever teste de exportação gerando arquivos Markdown e Excel**

- [x] **Step 2: Executar teste e verificar falha**
Run: `pytest tests/test_competitor_export.py`
Expected: FAIL

- [x] **Step 3: Implementar renderizadores Rich e exportadores OpenPyXL / Markdown**

- [x] **Step 4: Executar testes e verificar que passam**
Run: `pytest tests/test_competitor_export.py`
Expected: PASS

- [x] **Step 5: Commit**
`git add src/competitors/formatters.py src/competitors/exporter.py tests/test_competitor_export.py; git commit -m "feat(competitors): add rich terminal formatters and dossier exporters"`

---

### Task 6: Integração CLI (`src/cli/main.py`) e Subcomando `concorrencia`

**Files:**
- Modify: `src/cli/main.py`
- Test: `tests/test_competitor_cli.py`

**Interfaces:**
- Adiciona o subcomando `concorrencia`:
  - `--url`: Link de produto para dissecar.
  - `--termo`: Busca direta de nicho.
  - `--exportar`: Salva `dossie_mercado.md` e `benchmarking_concorrencia.xlsx`.
  - `--buscar-fabricas`: Aciona busca no Alibaba/AliExpress para preencher as recomendações de fábrica.

- [x] **Step 1: Escrever teste de integração da CLI para os argumentos de `concorrencia`**

- [x] **Step 2: Executar teste e verificar falha**
Run: `pytest tests/test_competitor_cli.py`
Expected: FAIL

- [x] **Step 3: Atualizar `src/cli/main.py` com `argparse` subparsers para manter compatibilidade com a busca legada**

- [x] **Step 4: Executar toda a suíte de testes do projeto (`pytest`) para garantir regressão zero**
Run: `pytest`
Expected: 100% dos testes passando (existentes + novos)

- [x] **Step 5: Commit**
`git add src/cli/main.py tests/test_competitor_cli.py; git commit -m "feat(cli): integrate competitor intelligence subcommand"`
