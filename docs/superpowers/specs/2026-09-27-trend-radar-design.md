# Trend Radar — Design Spec

> **Subsistema de detecção automática de tendências emergentes na China com cruzamento de vácuo de mercado no Brasil.**

## Contexto

O projeto `aliexpress-finder` já possui scrapers de AliExpress e Alibaba, cruzamento com o Mercado Livre (arbitragem), motor tributário brasileiro completo e dashboard web com duas abas (Radar ML e Arbitragem). Hoje, porém, toda análise é sob demanda: o usuário digita um termo e recebe os resultados naquele momento.

O Trend Radar resolve um problema diferente: **detectar automaticamente** quais produtos estão acelerando em vendas na China **antes** de chegarem ao Brasil, identificando oportunidades de primeiro entrante (First-Mover Advantage).

## Decisões de Design

| Decisão | Escolha |
|:---|:---|
| Descoberta de produtos | Automática — busca por lista de ~60 termos genéricos em 8 categorias |
| Frequência de coleta | Diária (4h AM horário Brasil) |
| Fontes chinesas | AliExpress + Alibaba |
| Alertas | Apenas no dashboard (sem e-mail) |
| Retenção de histórico | 90 dias |
| Escopo de categorias | Amplo — Eletrônicos, Casa, Moda, Beleza, Ferramentas, Pet, Esporte, Bebê |

## Arquitetura

O subsistema opera em 3 estágios sequenciais executados diariamente:

### Estágio 1 — Coleta China

O collector lê os termos ativos da tabela `trend_terms` e, para cada termo, executa buscas no AliExpress (`DirectAliExpressClient`) e Alibaba (`DirectAlibabaClient`), coletando os top 20 resultados de cada. Os dados brutos são gravados na tabela `trend_snapshots`.

**Salvaguardas contra bloqueio:**
- Sleep randomizado de 2-5s entre requisições
- Divisão em blocos de 15 termos com pausa de 10-15min entre blocos
- Horário off-peak: 4h AM (horário Brasil)
- Detecção de captcha/bloqueio: para o bloco atual, pula para o próximo, marca termos para re-tentativa
- Lock de processo via `flock` para evitar execuções concorrentes

**Volume estimado:** ~1500-3000 snapshots/dia.

### Estágio 2 — Cálculo de Velocidade

Para cada produto com ≥2 snapshots em datas diferentes:
- `sales_velocity_7d` = vendas_hoje − vendas_7_dias_atrás
- `sales_velocity_30d` = vendas_hoje − vendas_30_dias_atrás
- `acceleration` = (velocidade_semana_atual − velocidade_semana_anterior) / velocidade_semana_anterior × 100

Filtra produtos abaixo do threshold mínimo: `MIN_TREND_VELOCITY = 100` vendas/7d (constante em `src/trends/velocity.py`). Apenas produtos acima deste limiar passam para o Estágio 3.

### Estágio 3 — Gap Analysis Brasil

Para os top 100 produtos acelerados (constante `MAX_GAP_ANALYSIS = 100` em `gap_analyzer.py`, ordenados por velocidade decrescente):
1. Traduz título CN → PT usando `TRANSLATION_MAP` existente (expandido com termos adicionais)
2. Chama `CompetitorRadar.find_competitors(termo_pt)` no Mercado Livre
3. Calcula custo desembarcado via `ArbitrageEngine.calculate_landed_costs()`
4. Calcula Trend Score e classifica a oportunidade
5. Grava resultado em `trend_opportunities`

## Estrutura de Dados (SQLite)

Três novas tabelas no banco existente `data/mercado_livre_radar.db`:

### trend_terms

```sql
CREATE TABLE trend_terms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    term        TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'both',  -- 'ali', 'alibaba', 'both'
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    last_hit_at TEXT
);
```

### trend_snapshots

```sql
CREATE TABLE trend_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id         INTEGER NOT NULL REFERENCES trend_terms(id),
    source          TEXT NOT NULL,              -- 'aliexpress' ou 'alibaba'
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
CREATE INDEX idx_snapshots_product ON trend_snapshots(source, product_id, collected_at);
CREATE INDEX idx_snapshots_term    ON trend_snapshots(term_id, collected_at);
```

### trend_opportunities

```sql
CREATE TABLE trend_opportunities (
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
CREATE INDEX idx_opportunities_strategy ON trend_opportunities(strategy, trend_score DESC);
```

## Lista de Termos Padrão

~60 termos em 8 categorias:

| Categoria | Termos |
|:---|:---|
| Eletrônicos | `wireless earbuds`, `phone holder`, `portable charger`, `led strip lights`, `smart watch`, `bluetooth speaker`, `ring light`, `mini projector` |
| Casa & Cozinha | `kitchen gadget`, `organizer storage`, `silicone mold`, `electric kettle`, `mini blender`, `vacuum sealer`, `spice rack`, `coffee accessories` |
| Beleza & Saúde | `hair straightener brush`, `facial massager`, `nail art kit`, `makeup organizer`, `teeth whitening`, `scalp massager`, `beauty blender`, `lash curler` |
| Moda & Acessórios | `polarized sunglasses`, `automatic watch`, `crossbody bag`, `minimalist wallet`, `stainless steel ring`, `silk scarf`, `bucket hat` |
| Ferramentas | `laser level`, `electric screwdriver`, `soldering kit`, `digital caliper`, `heat gun`, `wire stripper`, `multimeter` |
| Pet | `automatic pet feeder`, `dog harness`, `cat toy interactive`, `pet grooming`, `dog training collar`, `cat water fountain` |
| Esporte & Outdoor | `resistance bands`, `jump rope`, `hiking backpack`, `camping light`, `yoga mat`, `fishing lure set`, `bike light` |
| Bebê & Criança | `baby carrier`, `educational toy`, `kids tablet`, `baby monitor`, `stroller organizer`, `teething toy` |

## Scoring: Trend Score (0-100)

```
Trend Score = (Velocidade × 0.40) + (Vácuo BR × 0.35) + (Viabilidade × 0.25)
```

| Sinal | Peso | Cálculo | Score = 100 | Score = 0 |
|:---|:---|:---|:---|:---|
| Velocidade | 40% | Δ vendas/7d normalizado pelo máximo da categoria | +10.000 vendas/semana | Δ vendas ≤ 0 |
| Vácuo BR | 35% | Inverso do nº de concorrentes no ML | 0 concorrentes | ≥ 50 concorrentes |
| Viabilidade | 25% | Margem líquida estimada | Margem ≥ 50% | Margem ≤ 0% |

### Classificação

| Faixa | Estratégia | Significado |
|:---|:---|:---|
| ≥ 75 | OCEANO_AZUL | Alta velocidade China + zero concorrência BR + margem boa |
| 50–74 | TENDENCIA | Crescimento forte China, pouca concorrência BR |
| 25–49 | EMERGENTE | Aceleração detectada, mercado BR já tem presença |
| < 25 | SATURADO | Crescimento baixo ou mercado BR cheio |

## Componentes Back-end

### Novos módulos (`src/trends/`)

| Módulo | Responsabilidade |
|:---|:---|
| `__init__.py` | Exports do pacote |
| `models.py` | Dataclasses: `TrendTerm`, `TrendSnapshot`, `TrendVelocity`, `TrendOpportunity` |
| `terms.py` | Lista `DEFAULT_TERMS` e função `seed_terms(repo)` |
| `repository.py` | CRUD SQLite: `save_snapshots()`, `get_velocity_data()`, `save_opportunities()`, `get_trending()`, `get_product_history()`, `cleanup_old(days=90)`, `seed_default_terms()`, `get_terms()` |
| `collector.py` | Estágio 1: lê termos → busca AliExpress/Alibaba → grava snapshots. Throttling, blocos, detecção de captcha. |
| `velocity.py` | Estágio 2: calcula Δ vendas/7d, Δ vendas/30d, aceleração. Filtra por threshold. |
| `gap_analyzer.py` | Estágio 3: traduz títulos → busca ML via CompetitorRadar → calcula landed cost → grava oportunidades |
| `scoring.py` | Trend Score composto e classificação |

### Integração CLI

Novo subcomando `trends` em `src/cli/main.py`:

```bash
python -m src.cli.main trends --collect    # Roda os 3 estágios completos
python -m src.cli.main trends --analyze    # Só recalcula velocidades e oportunidades
python -m src.cli.main trends --cleanup    # Remove dados > 90 dias
```

### Deploy (systemd)

- `deploy/trend-radar.timer`: dispara diariamente às 4h AM (America/Sao_Paulo), `Persistent=true`, `RandomizedDelaySec=15m`
- `deploy/trend-radar.service`: `Type=oneshot`, com `flock` em `/opt/aliexpress-finder/data/trends.lock`

### Novos endpoints API

Adicionados em `src/mercado_livre/dashboard_api.py`:

| Método | Rota | Retorno |
|:---|:---|:---|
| GET | `/radar/api/trends` | Lista de oportunidades classificadas (top 100). Query params: `?strategy=OCEANO_AZUL`, `?category=Casa` |
| GET | `/radar/api/trends/{product_id}/history` | Série temporal de 90 dias: vendas, velocidade, preço |
| GET | `/radar/api/trends/stats` | KPIs: total monitorado, oceanos azuis, top acelerações, distribuição por categoria |
| GET | `/radar/api/trends/terms` | Termos ativos com última coleta e contagem de hits |

## Componentes Front-end

### Novos arquivos

| Arquivo | Responsabilidade |
|:---|:---|
| `dashboard/src/components/TrendsView.tsx` | Componente principal: KPIs + filtros + tabela + expansão de detalhes |
| `dashboard/src/components/TrendCard.tsx` | Card individual de oportunidade (usado na tabela expandida) |
| `dashboard/src/components/VelocitySparkline.tsx` | Mini gráfico de vendas acumuladas (Recharts, 90 dias) |
| `dashboard/src/components/TrendFilters.tsx` | Barra de filtros por categoria e estratégia |

### Novas interfaces TypeScript (`types.ts`)

```typescript
interface TrendOpportunity {
  product_id: string
  source: string
  title: string
  url: string
  category: string
  price_brl: number
  sales_total: number
  sales_velocity_7d: number
  sales_velocity_30d: number
  acceleration: number
  ml_query: string
  ml_competitors: number
  ml_avg_price: number
  ml_full_share_pct: number
  landed_cost_brl: number
  suggested_price_brl: number
  net_margin_pct: number
  strategy: string
  trend_score: number
  supplier_name?: string
  moq?: number
  is_verified?: boolean
  sparkline: number[]
}

interface TrendStats {
  total_monitored: number
  ocean_blue_count: number
  trending_count: number
  emerging_count: number
  top_acceleration: { title: string; velocity_7d: number }
  by_category: { category: string; count: number }[]
  last_collection: {
    status: 'running' | 'completed' | 'failed'
    started_at: string
    finished_at: string | null
  }
}

interface TrendHistoryPoint {
  date: string
  sales_total: number
  price_brl: number
  velocity_7d: number | null
}
```

### Modificações em arquivos existentes

| Arquivo | Mudança |
|:---|:---|
| `App.tsx` | Expandir `activeTab` union para incluir `"trends"`, adicionar fetch `/radar/api/trends`, renderizar `<TrendsView>` condicionalmente |
| `Navbar.tsx` | Adicionar pill "🔥 Tendências" com ícone `TrendingUp` do Lucide |
| `types.ts` | Adicionar as 3 interfaces acima |

### Layout da aba Tendências

- **4 KPI cards** no topo: Produtos Monitorados, Oceanos Azuis, Tendências, Top Aceleração da Semana
- **Barra de filtros**: pills por estratégia (Todos / Oceano Azul / Tendência / Emergente), dropdown de categoria, campo de busca textual
- **Tabela**: colunas Score, Produto (com sparkline inline), Vendas China, Velocidade 7d, Concorrentes BR, Custo BR, Margem Líquida
- **Expansão de linha**: detalhes completos com links para fornecedor e concorrente ML, cálculo tributário e gráfico de 90 dias

## Tratamento de Erros

### Collector (Estágio 1)
- Captcha/bloqueio: para bloco atual, pula para o próximo após pausa de 15min
- Timeout de rede: 3 retries com backoff exponencial (2s, 4s, 8s)
- Produto sem vendas: grava com `sales_total = NULL`, velocity ignora
- Termo sem resultados por 30 dias: desativado automaticamente
- Coleta interrompida: snapshots já gravados por bloco, UNIQUE previne duplicatas

### Gap Analyzer (Estágio 3)
- ML bloqueado: fallback Bing (já existente), ou grava com `ml_competitors = NULL` e `strategy = 'PENDENTE'`
- Tradução ruim: flag `translation_confidence = 'low'` quando >70% de stop words removidas
- Câmbio indisponível: fallback `DEFAULT_USD_BRL` do config

### API e Dashboard
- Banco vazio: retorna listas vazias, dashboard mostra empty state
- Coleta em andamento: campo `last_collection.status` nos stats
- Sparkline com poucos pontos: renderiza normalmente com os pontos disponíveis

## Testes

### Unitários (~25-30 testes)
- `test_velocity.py`: cálculo de Δ vendas, aceleração, edge cases (1 snapshot, NULL, vendas decrescentes)
- `test_scoring.py`: Trend Score, pesos, classificação por faixa
- `test_gap_analyzer.py`: tradução, cruzamento ML, classificação com 0 vs muitos concorrentes
- `test_repository.py`: CRUD, deduplicação UNIQUE, cleanup 90d, seed de termos
- `test_collector.py`: blocos, throttling, captcha, parada graciosa
- `test_terms.py`: seed padrão, desativação automática
- `test_models.py`: serialização dataclasses

### Integração (~5-8 testes)
- `test_pipeline_integration.py`: 3 estágios em sequência com scrapers mockados
- `test_api_trends.py`: 4 endpoints com banco pré-populado, filtros, resposta vazia
- `test_dashboard_data_trends.py`: cleanup de 90 dias

### E2E (Playwright)
- `test_trends_tab.spec.ts`: navegação, KPIs, filtro por categoria, expansão de produto, sparkline

## Fora de Escopo

- Notificações por e-mail
- Edição de termos via dashboard (editáveis via CLI/SQL)
- Integração com Amazon BR ou Shopee
- Machine learning / previsão de tendências
- Termos manuais adicionados pelo usuário via interface (possível evolução futura)
