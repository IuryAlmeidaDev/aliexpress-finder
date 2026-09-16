---
id: guia-cli-comandos
title: Guia Completo da CLI & Comandos
sidebar_position: 8
---

# Guia Completo da CLI & Comandos

A interface de linha de comando (CLI) do **AliExpress & Alibaba Finder** é modular, rápida e pensada para o fluxo diário de mineração de produtos e tomada de decisões.

---

## 📌 Comandos Principais

### 1. Mineração no AliExpress (B2C)

```bash
# Busca básica
python -m src.cli.main --busca "<TERMO>"

# Busca com modo Choice (Imposto de Importação zerado) e margem de 50%
python -m src.cli.main --busca "<TERMO>" --choice --margem 50

# Busca com filtros de segurança e termos obrigatórios
python -m src.cli.main --busca "<TERMO>" --incluir "safira, aço" --excluir "pulseira" --min-nota 4.8 --min-vendas 50

# Exportar resultados para planilha Excel (oportunidades_aliexpress.xlsx)
python -m src.cli.main --busca "<TERMO>" --exportar
```

---

### 2. Atacado no Alibaba (B2B)

```bash
# Busca de atacado com limite de pedido mínimo (MOQ)
python -m src.cli.main --fonte alibaba --busca "<TERMO>" --max-moq 100

# Busca de alta segurança fabril (Verified Suppliers + Trade Assurance)
python -m src.cli.main --fonte alibaba --busca "<TERMO>" --verificados --trade-assurance --exportar
```

---

### 3. Inteligência de Concorrência & Benchmarking

```bash
# Dissecando um link de anúncio concorrente (Mercado Livre ou loja virtual)
python -m src.cli.main concorrencia --url "<LINK_DO_PRODUTO>" --exportar

# Pesquisa direta por nicho com mapeamento de fábricas na China
python -m src.cli.main concorrencia --termo "<PALAVRA_CHAVE>" --buscar-fabricas --exportar
```

---

### 4. Radar de Demanda no Mercado Livre

```bash
# Varredura do radar de categorias
python -m src.cli.main --fonte mercado-livre

# Execução em modo semanal com limite de categorias
python -m src.cli.main --fonte mercado-livre --ml-mode weekly --ml-max-categories 15
```

---

## 📋 Tabela de Parâmetros e Flags

| Flag | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--busca` | Texto | `""` | Termo de busca de produto para AliExpress ou Alibaba. |
| `--fonte` | Escolha | `ali` | Fonte de prospecção: `ali` (AliExpress), `alibaba` (Alibaba B2B) ou `mercado-livre`. |
| `--choice` | Booleano | `False` | Aplica o subsídio Choice (Imposto de Importação = R$ 0,00, apenas ICMS). |
| `--incluir` | Texto | `""` | Termos obrigatórios separados por vírgula (ex: `"safira, 316l"`). |
| `--excluir` | Texto | `""` | Termos proibidos separados por vírgula (ex: `"pulseira, vidro"`). |
| `--margem` | Decimal | `40.0` | Margem líquida mínima desejada sobre a venda (em %). |
| `--max-custo` | Decimal | `None` | Custo final máximo tolerado em R$ no Brasil. |
| `--min-vendas` | Inteiro | `.env` | Quantidade mínima de vendas do produto para passar no filtro. |
| `--min-nota` | Decimal | `.env` | Nota mínima de avaliação do anúncio ou vendedor (ex: `4.7`). |
| `--max-moq` | Inteiro | `None` | Quantidade máxima de pedido mínimo permitida no Alibaba. |
| `--verificados` | Booleano | `False` | Filtra apenas fornecedores certificados (*Verified Suppliers*) no Alibaba. |
| `--trade-assurance` | Booleano | `False` | Filtra apenas fornecedores com garantia comercial *Trade Assurance*. |
| `--exportar` | Booleano | `False` | Salva os resultados em arquivo Excel ou Markdown executivo. |

### Flags do Subcomando `concorrencia`:

| Flag | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--url` | Texto | `""` | URL do produto concorrente para dissecar (Mercado Livre ou site próprio). |
| `--termo` | Texto | `""` | Termo ou nicho de concorrência direto. |
| `--limite` | Inteiro | `5` | Número de concorrentes mapeados no ranking. |
| `--buscar-fabricas` | Booleano | `False` | Consulta fornecedores industriais equivalentes na China. |
| `--margem` | Decimal | `35.0` | Margem desejada para cálculo do teto de custo fabril FOB. |
| `--usd` | Decimal | `5.50` | Cotação do Dólar para cálculo da conversão. |
