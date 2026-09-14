# Especificação Técnica: Módulo de Atacado Alibaba B2B (Alibaba Finder)

**Data:** 14/09/2026  
**Status:** Aprovado para Planejamento  
**Autor:** Antigravity  
**Repositório:** `aliexpress-finder`

---

## 1. Visão Geral e Objetivos

Expandir a ferramenta de garimpo de oportunidades para incluir o **Alibaba.com** como uma fonte dedicada e independente para compras B2B / Atacado direto de fabricantes e indústrias chinesas.

### 1.1 Objetivos (Goals)
- Manter **separação estrita** entre a busca no AliExpress (B2C / Varejo / Remessa Conforme) e a busca no Alibaba (B2B / Atacado / Lote / Fabricante).
- Coletar dados essenciais de atacado: **Preço Unitário**, **MOQ (Pedido Mínimo / Quantidade Mínima)**, **Nome da Fábrica**, selos **Verified Supplier**, **Trade Assurance** e **Anos de Empresa**.
- Permitir filtros específicos de atacado via CLI: `--max-moq` (lote máximo aceitável), `--verificados` (apenas Verified Supplier) e `--trade-assurance`.
- Calcular o **investimento total do lote** e o **custo unitário desembarcado**, aplicando a tributação de importação simplificada (Regime de Tributação Simplificada - RTS: 60% II + ICMS "por dentro").
- Projetar o faturamento e o lucro líquido do lote inteiro na revenda no mercado brasileiro com base na margem desejada.
- Exibir tabela Rich customizada para B2B e exportar os resultados para [`oportunidades_alibaba.xlsx`](file:///C:/Users/iuryc/projects/aliexpress-finder/oportunidades_alibaba.xlsx).
- Não quebrar nem introduzir regressões na busca existente do AliExpress (`pytest` 100% verde).

### 1.2 Não-Objetivos (Non-Goals)
- Não mesclar resultados do AliExpress e do Alibaba na mesma tabela ou na mesma planilha (cada plataforma tem sua própria execução e regras).
- Não realizar automação de checkout ou compra direta (a ferramenta é um radar de prospecção analítica e geração de relatórios com links para negociação).

---

## 2. Arquitetura e Fluxo de Dados

```
CLI Entrypoint (src/cli/main.py)
   │
   ├── Flag --fonte ali (Padrão)
   │     └── DirectAliExpressClient / OfficialAliExpressClient
   │           └── FilterPipeline (Reputação / Anti-Trick)
   │                 └── Remessa Conforme Tax Engine
   │                       └── render_results_table -> oportunidades_aliexpress.xlsx
   │
   └── Flag --fonte alibaba
         └── DirectAlibabaClient (src/clients/alibaba_scraper.py)
               └── AlibabaFilterPipeline (src/filters/alibaba_pipeline.py)
                     └── Wholesale Financial Engine (src/finance/taxes.py + margins.py)
                           └── render_alibaba_table -> oportunidades_alibaba.xlsx
```

---

## 3. Especificação dos Componentes

### 3.1 Cliente de Busca Alibaba (`src/clients/alibaba_scraper.py`)
- Classe `DirectAlibabaClient(BaseSearchClient)`:
  - **URL de Busca:** `https://www.alibaba.com/trade/search?SearchText={query}`.
  - **Mecanismo Stealth:** Utiliza `curl_cffi` com impersonação TLS `chrome124` e cabeçalhos de navegador modernos.
  - **Função `parse_moq(moq_str: str) -> int`:**
    - Converte strings como `"Min. order: 50 pieces"`, `"MOQ: 10 sets"`, `"100 pcs"` em inteiro (`50`, `10`, `100`).
    - Caso não encontre MOQ explícito, assume `1` por segurança.
  - **Função `parse_alibaba_price(price_str: str, usd_rate: float) -> float`:**
    - Suporta valores diretos em R$ ou valores em US$ (ex: `"$1.20 - $2.50"` captura o menor valor `$1.20` e converte para BRL usando a cotação).
  - **Função `parse_alibaba_html_items(html: str, usd_rate: float) -> List[Dict[str, Any]]`:**
    - Extrai para cada card:
      - `id`: ID do produto no Alibaba.
      - `title`: Título do produto.
      - `price`: Preço unitário em BRL.
      - `moq`: Quantidade mínima de pedido (inteiro).
      - `supplier_name`: Nome da fábrica ou fornecedor.
      - `is_verified`: Booleano (selo `Verified`).
      - `has_trade_assurance`: Booleano (selo `Trade Assurance`).
      - `years_in_business`: Número de anos no Alibaba (ex: `5`).
      - `url`: Link direto para o produto.

### 3.2 Pipeline de Filtros B2B (`src/filters/alibaba_pipeline.py`)
- Classe `AlibabaFilterPipeline`:
  - **Parâmetros:** `max_moq: Optional[int] = None`, `only_verified: bool = False`, `only_trade_assurance: bool = False`.
  - **Filtro de MOQ:** Se `max_moq` estiver definido, descarta itens onde `item["moq"] > max_moq`.
  - **Filtro Verified:** Se `only_verified` for `True`, descarta itens onde `item["is_verified"] == False`.
  - **Filtro Trade Assurance:** Se `only_trade_assurance` for `True`, descarta itens onde `item["has_trade_assurance"] == False`.
  - **Filtro Semântico:** Reaproveita `matches_semantic_criteria` para inclusão obrigatória (`--incluir`) e exclusão de termos proibidos (`--excluir`).

### 3.3 Motor Financeiro de Lote (`src/finance/`)
- No caso de compras no atacado B2B via Alibaba:
  - **Investimento de Compra (FOB Lote):** `Preço Unitário × MOQ`.
  - **Tributação de Importação B2B:**
    - Aplica o cálculo oficial do Regime de Tributação Simplificada (RTS): 60% de Imposto de Importação sobre o lote + ICMS "por dentro" (alíquota configurada, padrão 17%).
  - **Custo Final Total do Lote (Landed Cost Lote):** `FOB Lote + Impostos Totais`.
  - **Custo Unitário Desembarcado:** `Custo Final Total do Lote / MOQ`.
  - **Projeção de Venda e Margem do Lote:**
    - `Preço Sugerido Venda Unitária`: simulado com margem desejada (ex: 40%) e taxa de marketplace (16%).
    - `Faturamento Projetado do Lote`: `Preço Sugerido Venda Unitária × MOQ`.
    - `Lucro Líquido do Lote (R$)`: Lucro líquido após venda de todas as unidades.
    - `ROI do Lote (%)`: Retorno sobre o capital investido.

### 3.4 Formatação e CLI (`src/cli/`)
- **CLI Flags Adicionadas (`src/cli/main.py`):**
  - `--fonte`: Escolhe entre `ali` (padrão) e `alibaba`.
  - `--max-moq`: Quantidade máxima permitida para o pedido mínimo (ex: `--max-moq 50`).
  - `--verificados`: Flag booleana que restringe para fábricas Verified.
  - `--trade-assurance`: Flag booleana que restringe para fornecedores com garantia Trade Assurance.
- **Tabela Terminal B2B (`src/cli/formatters.py`):**
  - Função `render_alibaba_table(records)`:
    - Colunas: `Produto / Fábrica`, `MOQ`, `Preço Unit. Ali`, `Custo Unit. Final`, `Lote Total (R$)`, `Venda Sug. (Un.)`, `Lucro Lote (R$)`, `ROI (%)`, `Selos`, `Link`.
- **Exportador Excel (`src/cli/exporter.py`):**
  - Quando `--fonte alibaba` for selecionado, o arquivo de exportação será nomeado automaticamente como [`oportunidades_alibaba.xlsx`](file:///C:/Users/iuryc/projects/aliexpress-finder/oportunidades_alibaba.xlsx).

---

## 4. Estratégia de Testes

1. **`tests/test_alibaba_scraper.py`:**
   - Teste unitário de parsing de MOQ com múltiplos formatos (`"Min. order: 50 pieces"`, `"100 sets"`, `"1 piece"`).
   - Teste unitário de conversão de preço e ranges em USD/BRL.
   - Teste unitário de extração de fornecedores, selos Verified e Trade Assurance a partir de mock de HTML.
2. **`tests/test_alibaba_filters.py`:**
   - Teste de aceitação e descarte por `--max-moq`.
   - Teste de filtro booleano de Verified e Trade Assurance.
   - Teste de integração de termos semânticos inclusivos/exclusivos no pipeline do Alibaba.
3. **`tests/test_alibaba_cli.py`:**
   - Execução do fluxo completo da CLI com `--fonte alibaba`.
   - Validação de que a saída do terminal é renderizada e o arquivo `oportunidades_alibaba.xlsx` é criado.
   - Validação de isolamento: garantia de que `--fonte ali` continua intocado.

---

## 5. Critérios de Aceite

1. Executar `python -m src.cli.main --fonte alibaba --busca "relogio infantil" --max-moq 100 --exportar` com sucesso gerando a tabela B2B e o arquivo `oportunidades_alibaba.xlsx`.
2. O sistema existente do AliExpress permanece funcionando com 100% dos testes unitários e de integração passando.
3. Todos os novos testes cobrindo o Alibaba passam sem erros (`pytest -v`).
