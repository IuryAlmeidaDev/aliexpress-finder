# AliExpress & Alibaba B2B Resale Opportunity Finder & Tax Calculator 🇧🇷

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-55%20passed%20(100%25)-brightgreen?logo=pytest&logoColor=white)](tests/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()

> **Ferramenta CLI profissional para mineração de produtos, filtragem inteligente e análise de viabilidade financeira de importações no AliExpress (Varejo/B2C) e Alibaba (Atacado/B2B), com foco no mercado brasileiro de revenda (Mercado Livre, Shopee, Amazon Brasil e e-commerce próprio).**

---

## 📌 Visão Geral

O cenário de importação no Brasil para revendedores exige precisão cirúrgica de dados e conformidade tributária:
1. **No Varejo (AliExpress B2C):** Aplicam-se as regras do **Remessa Conforme** (20% até US$ 50 com dedução de US$ 20 acima de US$ 50) ou subsídio integral de II no **Modo Choice**, além do ICMS estadual calculado "por dentro". Anúncios ardilosos frequentemente vendem peças ou pulseiras com o título e foto do produto completo a preços irrealistas.
2. **No Atacado (Alibaba B2B):** Não há isenção do Remessa Conforme; opera-se sob o regime de **Importação Formal de Atacado (RTS)** com alíquota cheia de 60% de Imposto de Importação + ICMS por dentro, exigindo análise de **Quantidade Mínima de Pedido (MOQ)**, investimento total em lote e auditoria de fornecedor (*Verified Supplier* e *Trade Assurance*).

Este sistema unifica as duas operações em uma única CLI modular, filtrando ruídos, calculando custos desembarcados exatos e projetando margens líquidas reais e ROI.

---

## 🚀 Funcionalidades Principais

### 1. Prospecção Multicanal (B2C & B2B)
- **AliExpress B2C (`--fonte ali`, padrão):**
  - Focado em compras individuais, testes de nicho e dropshipping.
  - Funciona imediatamente via **Scraper Direto (Stealth)** com headers e impersonação de navegador (`chrome124`) sem necessidade de chaves.
  - Suporte ao **Conector Oficial TOP Protocol** com assinatura criptográfica HMAC-SHA256, pronto para plugar credenciais quando aprovado no portal de desenvolvedores.
  - Identifica e aplica o subsídio do **AliExpress Choice** (`--choice`), zerando o Imposto de Importação e cobrando apenas o ICMS.
- **Alibaba B2B Atacado (`--fonte alibaba`):**
  - Focado em importação comercial em escala direto de fabricantes.
  - Extração automatizada de faixas de preço de fábrica, Quantidade Mínima de Pedido (**MOQ**), anos de empresa e selos de garantia (*Verified Supplier* e *Trade Assurance*).
  - Simulação de viabilidade financeira por **Lote Fechado** e revenda unitária fracionada.

### 2. Pipeline de Filtros Inteligentes
- **🛡️ Anti-Trick (Anti-Pegadinha):** Algoritmo heurístico que detecta e descarta anúncios que vendem apenas acessórios (ex: pulseiras, caixas vazias, vidros de reposição ou ferramentas) quando o usuário busca pelo produto principal (ex: relógios, smartphones).
- **🔤 Filtro Semântico Multilíngue:** Dicionário bidirecional de sinônimos cruzados em Português e Inglês (ex: `safira` $\leftrightarrow$ `sapphire`, `estéril`/`sem logo` $\leftrightarrow$ `sterile dial`, `automático` $\leftrightarrow$ `nh35`/`miyota`, `316l` $\leftrightarrow$ `aço`). Suporta termos obrigatórios (`--incluir`) e termos proibidos (`--excluir`).
- **⭐ Filtro de Reputação (B2C):** Restringe a busca por nota mínima de avaliação e volume mínimo de vendas.
- **🏭 Filtro de Escala e Segurança Fabril (B2B):** Teto de MOQ (`--max-moq`), fornecedores auditados presencialmente (`--verificados`) e garantia comercial (`--trade-assurance`).

### 3. Motores Tributários Brasileiros Precisos
- **Cálculo de ICMS "Por Dentro" (Gross-Up):** Aplica a fórmula legal em que o tributo estadual integra a sua própria base de cálculo: $\text{Base} = \frac{V_{ad} + II}{1 - \text{ICMS}}$.
- **Isolamento de Regimes:**
  - Varejo: Tabela progressiva do Remessa Conforme + benefício Choice.
  - Atacado: Alíquota fixa de 60% de Imposto de Importação sobre a base completa do lote.

### 4. Simulador de Viabilidade, Margem e ROI
- Cálculo do **Preço Sugerido de Venda** considerando a comissão da plataforma de revenda (ex: 16% Mercado Livre / Shopee) e a margem líquida pretendida (ex: 40%).
- Exibição de **Lucro Líquido Unitário/Lote** e **Retorno sobre o Investimento (ROI %)**.

### 5. Saída Visual Rica e Exportação
- Tabelas coloridas, responsivas e estilizadas no terminal via `rich`.
- Exportação estruturada para planilhas Excel (`.xlsx`):
  - B2C: `oportunidades_aliexpress.xlsx`
  - B2B: `oportunidades_alibaba.xlsx`

---

## 🖥️ Demonstração Visual das Tabelas no Terminal

### A. Tabela de Oportunidades AliExpress (Varejo B2C)
```text
                  💎 Melhores Oportunidades Encontradas no AliExpress (Custo Brasil & Margem)                  
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Produto                             ┃ Preço Ali ┃ Impostos ┃ Custo Final ┃ Sugestão Venda ┃ Lucro Líquido ┃    ROI ┃ Aval. ┃ Link  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ Pagani Design NH35 Safira Automático│ R$ 280.00 │ R$ 78.43 │  R$ 358.43  │   R$ 814.61    │   R$ 325.84   │  90.9% │ 4.8⭐ │ Abrir │
│ Addiesdive Relógio Mergulho 200m    │ R$ 195.50 │ R$ 54.74 │  R$ 250.24  │   R$ 568.72    │   R$ 227.49   │  90.9% │ 4.9⭐ │ Abrir │
│ Cadisen Vintage Mecânico Miyota     │ R$ 220.00 │ R$ 61.60 │  R$ 281.60  │   R$ 640.00    │   R$ 256.00   │  90.9% │ 4.7⭐ │ Abrir │
└─────────────────────────────────────┴───────────┴──────────┴─────────────┴────────────────┴───────────────┴────────┴───────┴───────┘
```

### B. Tabela de Oportunidades Alibaba (Atacado B2B)
```text
                      🏭 Oportunidades Atacado Alibaba.com (Fábrica & Custo de Lote)                           
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Produto / Fornecedor                ┃  MOQ  ┃ Preço Unit. (R$) ┃ Custo Unit. Final┃ Lote Total(R$) ┃ Sugestão Venda Un. ┃ Lucro Lote (R$)  ┃   ROI  ┃   Selos    ┃ Link  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│ Kids Silicone Waterproof Watch      │ 50 un │     R$ 8.50      │     R$ 16.39     │   R$ 819.28    │      R$ 37.24      │    R$ 573.49     │  70.0% │ 🛡️Verif 🤝TA│ Abrir │
│ Shenzhen Smart Watch Co., Ltd.      │       │                  │                  │                │                    │                  │        │ 5a         │       │
│ Bluetooth TWS Earbuds ANC           │ 30 un │     R$ 22.00     │     R$ 42.41     │  R$ 1,272.29   │      R$ 96.39      │    R$ 890.60     │  70.0% │ 🛡️Verif 🤝TA│ Abrir │
│ Dongguan Audio Tech Factory         │       │                  │                  │                │                    │                  │        │ 7a         │       │
└─────────────────────────────────────┴───────┴──────────────────┴──────────────────┴────────────────┴────────────────────┴──────────────────┴────────┴────────────┴───────┘
```

---

## 📁 Arquitetura e Estrutura do Código

O projeto segue princípios de **Clean Architecture**, alta coesão e baixo acoplamento:

```text
aliexpress-finder/
├── src/
│   ├── cli/
│   │   ├── exporter.py          # Exportação para planilhas Excel (pandas & openpyxl)
│   │   ├── formatters.py        # Tabelas coloridas no terminal com suporte a links (rich)
│   │   └── main.py              # CLI unificada (argparse) e orquestração de fluxo
│   ├── clients/
│   │   ├── alibaba_scraper.py   # Scraper stealth do Alibaba B2B (preço, faixas, MOQ, selos)
│   │   ├── base_client.py       # Interface abstrata comum para clientes de busca
│   │   ├── direct_scraper.py    # Scraper stealth HTTP do AliExpress com curl_cffi
│   │   └── official_api.py      # Conector oficial TOP Protocol (HMAC-SHA256)
│   ├── filters/
│   │   ├── alibaba_pipeline.py  # Pipeline B2B: MOQ, fornecedor auditado, Trade Assurance
│   │   ├── anti_trick.py        # Heurísticas de detecção de pegadinhas de acessórios
│   │   ├── pipeline.py          # Pipeline sequencial B2C do AliExpress
│   │   ├── reputation.py        # Filtro de nota de loja e volume de vendas
│   │   └── semantic.py          # Normalização textual e matriz de sinônimos bilíngues
│   ├── finance/
│   │   ├── margins.py           # Simulador financeiro unitário (venda, comissão, lucro, ROI)
│   │   ├── taxes.py             # Motor tributário B2C (Remessa Conforme + Choice + ICMS)
│   │   └── wholesale.py         # Motor tributário B2B (II fixo 60% + lote + ROI de atacado)
│   └── config.py                # Carregamento resiliente de configurações e variáveis de ambiente
├── tests/                       # Suíte completa de testes unitários e de integração
│   ├── test_alibaba_cli.py
│   ├── test_alibaba_filters.py
│   ├── test_alibaba_integration.py # Teste de integração ponta a ponta Alibaba B2B
│   ├── test_alibaba_scraper.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_direct_scraper.py
│   ├── test_filters.py
│   ├── test_integration.py         # Teste de integração ponta a ponta AliExpress B2C
│   ├── test_margins.py
│   ├── test_official_api.py
│   ├── test_taxes.py
│   └── test_wholesale_finance.py
├── .env.example                 # Modelo de variáveis de ambiente
├── pytest.ini                   # Configuração do executor de testes e PYTHONPATH
├── requirements.txt             # Dependências de produção e testes
└── README.md                    # Documentação oficial
```

---

## ⚙️ Instalação e Configuração

### 1. Pré-requisitos
- **Python:** Versão 3.10 ou superior.
- **Sistema Operacional:** Windows, Linux ou macOS.

### 2. Instalação Passo a Passo

```bash
# 1. Clone o repositório
git clone https://github.com/IuryAlmeidaDev/aliexpress-finder.git
cd aliexpress-finder

# 2. Crie o ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Windows (CMD):
.\venv\Scripts\activate.bat
# No Linux / macOS:
source venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração de Variáveis de Ambiente (`.env`)

Copie o arquivo de modelo para o seu ambiente local:

```bash
# Windows:
copy .env.example .env
# Linux / macOS:
cp .env.example .env
```

Conteúdo padrão do arquivo `.env`:

```ini
# Chaves da API Oficial do AliExpress (Opcional - deixe vazio para usar o Scraper Direto)
ALIEXPRESS_APP_KEY=
ALIEXPRESS_APP_SECRET=

# Parâmetros Financeiros Padrão
DEFAULT_USD_BRL=5.50
DEFAULT_ICMS_RATE=0.17
DEFAULT_MARKETPLACE_FEE=0.16
DEFAULT_TARGET_MARGIN=0.40

# Filtros Padrão de Reputação (AliExpress B2C)
MIN_STORE_RATING=4.5
MIN_SALES_COUNT=10
```

> [!NOTE]
> Se `ALIEXPRESS_APP_KEY` e `ALIEXPRESS_APP_SECRET` estiverem vazios, o sistema opera de forma transparente utilizando o **Scraper Direto de Alta Fidelidade**, sem necessidade de cadastro ou aprovação prévia.

---

## 📖 Guia de Uso da Linha de Comando (CLI)

### Tabela Completa de Opções

| Parâmetro | Tipo | Escopo | Padrão | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `--fonte` | Escolha | Global | `ali` | Fonte de busca: `ali` (AliExpress B2C) ou `alibaba` (Alibaba B2B Atacado). |
| `--busca` | Texto | Global | *Obrigatório* | Termo principal de busca (ex: `"relogio automatico"`, `"kids watch"`). |
| `--incluir` | Texto | Global | `""` | Termos obrigatórios separados por vírgula (ex: `"safira, sterile"`). |
| `--excluir` | Texto | Global | `""` | Termos proibidos separados por vírgula (ex: `"quartz, pulseira, strap"`). |
| `--max-custo`| Float | Global | `None` | Custo final unitário máximo aceito desembarcado em R$. |
| `--margem` | Float | Global | `40.0` | Margem líquida desejada na revenda em porcentagem (ex: `35` para 35%). |
| `--choice` | Flag | AliExpress | `False` | Aplica o subsídio Choice do AliExpress (Imposto de Importação zerado). |
| `--min-vendas` | Int | AliExpress | `.env` (10) | Volume mínimo de vendas que o anúncio deve possuir. |
| `--min-nota` | Float | AliExpress | `.env` (4.5) | Avaliação mínima da loja/produto (ex: `4.7`). |
| `--max-moq` | Int | Alibaba | `None` | Quantidade Mínima de Pedido (MOQ) máxima aceita (ex: `50`, `100`). |
| `--verificados`| Flag | Alibaba | `False` | Filtra apenas fornecedores com selo auditado *Verified Supplier*. |
| `--trade-assurance`| Flag | Alibaba | `False` | Filtra apenas fornecedores com proteção contratual *Trade Assurance*. |
| `--exportar` | Flag | Global | `False` | Salva os resultados em planilha Excel (`.xlsx`). |

---

### Exemplos Práticos por Cenário

#### 🅰️ AliExpress Varejo (B2C)

1. **Minerar Relógios Mecânicos com Vidro de Safira e Mostrador Estéril (Sem Logo):**
   ```bash
   python -m src.cli.main --fonte ali --busca "relogio automatico" --incluir "safira, sterile" --excluir "quartz, pulseira" --exportar
   ```

2. **Aproveitar o Subsídio Choice do AliExpress (Imposto de Importação R$ 0,00):**
   ```bash
   python -m src.cli.main --fonte ali --busca "relogio automatico" --choice --max-custo 220 --margem 35 --exportar
   ```

3. **Filtrar Fornecedores de Alta Reputação (Nota > 4.8 e Mais de 100 Vendas):**
   ```bash
   python -m src.cli.main --fonte ali --busca "fone bluetooth anc" --incluir "cancelamento ativo" --excluir "case, capa" --min-vendas 100 --min-nota 4.8 --exportar
   ```

#### 🅱️ Alibaba Atacado e Fábrica (B2B)

1. **Buscar Lotes de Relógios Infantis com Baixo MOQ em Fornecedores Auditados:**
   ```bash
   python -m src.cli.main --fonte alibaba --busca "kids watch silicone" --max-moq 50 --verificados --trade-assurance --exportar
   ```

2. **Prospecção de Fones TWS com Custo Unitário Desembarcado até R$ 30,00:**
   ```bash
   python -m src.cli.main --fonte alibaba --busca "tws earphones" --max-moq 100 --max-custo 30 --margem 50 --verificados --exportar
   ```

3. **Pesquisa de Gadgets Inovadores (Smart Rings) com Margem de 60%:**
   ```bash
   python -m src.cli.main --fonte alibaba --busca "smart ring" --max-moq 30 --trade-assurance --margem 60 --exportar
   ```

#### 🅲 Radar Mercado Livre para Marca Própria

O radar não compara preços com fornecedores estrangeiros. Ele descobre produtos já validados no Brasil e explica quais podem merecer investigação para desenvolver uma marca própria. A nota de demanda e a nota de potencial de marca são independentes, acompanhadas pela cobertura dos dados e pelas evidências encontradas.

Configure uma aplicação autorizada do Mercado Livre no `.env`:

```ini
MERCADO_LIVRE_ACCESS_TOKEN=
MERCADO_LIVRE_CLIENT_ID=
MERCADO_LIVRE_CLIENT_SECRET=
MERCADO_LIVRE_REFRESH_TOKEN=
MERCADO_LIVRE_TOKEN_FILE=data/mercado_livre_token.json
MERCADO_LIVRE_DB_PATH=data/mercado_livre_radar.db
MERCADO_LIVRE_REPORT_DIR=reports
MERCADO_LIVRE_CATEGORY_IDS=
```

Para a autorização inicial, cadastre na aplicação o redirect URI exato `https://api.monvix.me/oauth/mercado-livre/callback`, habilite PKCE e execute o assistente. O Client Secret não aparece na tela durante a digitação e as credenciais são gravadas no arquivo protegido usado pelas renovações automáticas:

```bash
python -m src.mercado_livre.oauth_setup
```

Execução autônoma, com descoberta de categorias:

```bash
python -m src.cli.main --fonte mercado-livre
```

Execução dirigida a categorias-folha específicas:

```bash
python -m src.cli.main --fonte mercado-livre --ml-category MLB1234 --ml-category MLB5678
```

Cada rodada gera um Excel com as abas `Oportunidades`, `Investigar`, `Evidências` e `Execução`, além de manter o histórico em SQLite. A primeira rodada informa que ainda não existe histórico semanal comparável. O timer disponível em `deploy/` roda às segundas-feiras, às 07:00 no horário de São Paulo, e usa o mesmo comando da execução manual.

---

## 🧮 Metodologia de Cálculo Financeiro e Tributário

### 1. AliExpress B2C: Regime Remessa Conforme

Aplicado quando `--fonte ali`:

#### A. Valor Aduaneiro ($V_{ad}$)
$$V_{ad\text{ (BRL)}} = \text{Preço do Produto} + \text{Frete}$$
$$V_{ad\text{ (USD)}} = \frac{V_{ad\text{ (BRL)}}}{\text{Cotação USD/BRL}}$$

#### B. Imposto de Importação (II)
- **Modo Choice (`--choice`):** $II = \text{R\$ } 0{,}00$ (subsidiado pela plataforma).
- **Remessas até US$ 50,00:**
  $$II = V_{ad\text{ (BRL)}} \times 0{,}20$$
- **Remessas acima de US$ 50,00:**
  $$II = \max\left(0\,,\; (V_{ad\text{ (BRL)}} \times 0{,}60) - (20{,}00 \times \text{Cotação USD/BRL})\right)$$

#### C. ICMS Calculado "Por Dentro" (Gross-Up)
$$\text{Base ICMS} = \frac{V_{ad\text{ (BRL)}} + II}{1 - \text{Alíquota ICMS}}$$
$$\text{Valor ICMS} = \text{Base ICMS} \times \text{Alíquota ICMS}$$

#### D. Custo Final Desembarcado Unitário (Landed Cost)
$$\text{Custo Final} = V_{ad\text{ (BRL)}} + II + \text{ICMS}$$

#### E. Formação de Preço de Venda e Margem Líquida
$$\text{Preço Sugerido de Venda} = \frac{\text{Custo Final}}{1 - \text{Taxa Marketplace} - \text{Margem Líquida Alvo}}$$
$$\text{Comissão Marketplace (R\$)} = \text{Preço Sugerido} \times \text{Taxa Marketplace}$$
$$\text{Lucro Líquido Unitário (R\$)} = \text{Preço Sugerido} - \text{Comissão Marketplace} - \text{Custo Final}$$
$$\text{ROI (\%)} = \left(\frac{\text{Lucro Líquido}}{\text{Custo Final}}\right) \times 100\%$$

---

### 2. Alibaba B2B: Atacado Formal e Lotes Industriais

Aplicado quando `--fonte alibaba`. Não há faixa de isenção nem deduções aduaneiras de pessoa física:

#### A. Imposto de Importação Fixo (60%)
$$II_{\text{unit}} = V_{ad\text{ (BRL)}} \times 0{,}60$$

#### B. ICMS Calculado "Por Dentro" sobre a Base Integral
$$\text{Base ICMS}_{\text{unit}} = \frac{V_{ad\text{ (BRL)}} + II_{\text{unit}}}{1 - \text{Alíquota ICMS}}$$
$$\text{ICMS}_{\text{unit}} = \text{Base ICMS}_{\text{unit}} \times \text{Alíquota ICMS}$$

#### C. Custo Unitário Final Desembarcado
$$\text{Custo Unitário Final} = V_{ad\text{ (BRL)}} + II_{\text{unit}} + \text{ICMS}_{\text{unit}}$$

#### D. Investimento Total do Lote (MOQ)
$$\text{Investimento Total Lote} = \text{Custo Unitário Final} \times MOQ$$

#### E. Simulação de Receita e Lucro do Lote na Revenda Fracionada
$$\text{Preço Unitário Sugerido} = \frac{\text{Custo Unitário Final}}{1 - \text{Taxa Marketplace} - \text{Margem Líquida Alvo}}$$
$$\text{Receita Bruta Total} = \text{Preço Unitário Sugerido} \times MOQ$$
$$\text{Comissão Marketplace Total} = \text{Receita Bruta Total} \times \text{Taxa Marketplace}$$
$$\text{Lucro Líquido do Lote} = \text{Receita Bruta Total} - \text{Comissão Marketplace Total} - \text{Investimento Total Lote}$$
$$\text{ROI do Lote (\%)} = \left(\frac{\text{Lucro Líquido do Lote}}{\text{Investimento Total Lote}}\right) \times 100\%$$

---

## 🧪 Qualidade de Código e Testes Automatizados

O projeto mantém uma suíte funcional com 66 testes automatizados (unitários, de borda e de integração ponta a ponta).

### Executar Toda a Suíte de Testes
```bash
python -m pytest -v
```

### Executar Testes por Categoria
```bash
# 1. Teste de integração ponta a ponta do AliExpress B2C
python -m pytest tests/test_integration.py -v

# 2. Teste de integração ponta a ponta do Alibaba B2B
python -m pytest tests/test_alibaba_integration.py -v

# 3. Testes do motor tributário
python -m pytest tests/test_taxes.py tests/test_wholesale_finance.py -v

# 4. Testes de filtros semânticos e anti-pegadinha
python -m pytest tests/test_filters.py tests/test_alibaba_filters.py -v

# 5. Radar Mercado Livre: cliente, pontuação, histórico e integração
python -m pytest tests/test_mercado_livre_*.py -v
```

---

## ❓ Perguntas Frequentes & Resolução de Problemas (FAQ)

<details>
<summary><b>1. Como resolver problemas de acentuação ou caracteres estranhos no Windows?</b></summary>

O sistema já força nativamente a reconfiguração de `stdout` e `stderr` para UTF-8 no Windows. No entanto, se o seu terminal PowerShell apresentar problemas visuais, execute antes de rodar os comandos:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```
</details>

<details>
<summary><b>2. Como conseguir as credenciais da API Oficial do AliExpress?</b></summary>

1. Cadastre-se no [AliExpress Open Platform](https://open.aliexpress.com/).
2. Solicite aprovação para o pacote de APIs de Afiliados / Produtos.
3. Preencha seu `App Key` e `App Secret` no arquivo `.env`.
4. Caso ainda não possua aprovação, o Scraper Direto do projeto funciona sem limites de autenticação.
</details>

<details>
<summary><b>3. Como o Scraper Direto lida com bloqueios (WAF/Cloudflare)?</b></summary>

O scraper utiliza `curl_cffi` com impersonação TLS e fingerprint JA3 do Chrome 124, simulando navegação legítima de desktop e contornando desafios WAF comuns do Alibaba e AliExpress.
</details>

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.

> *Aviso Legal: Esta ferramenta foi desenvolvida para auxílio em pesquisa de mercado, planejamento tributário e viabilidade financeira. Respeite sempre os termos de serviço e diretrizes de uso dos marketplaces consultados.*
