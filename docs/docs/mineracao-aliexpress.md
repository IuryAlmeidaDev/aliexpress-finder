---
id: mineracao-aliexpress
title: Mineração no AliExpress (B2C)
sidebar_position: 3
---

# Mineração no AliExpress (Varejo B2C)

O módulo de mineração do **AliExpress** é focado em testes de nicho, validação de produtos campeões com baixo risco financeiro e pedidos de amostras sob o regime do **Remessa Conforme**.

---

## 🛠️ Arquitetura de Conectores

O sistema opera com uma estratégia de fallback inteligente:

1. **Scraper Direto (Stealth):**
   * Utiliza a biblioteca `curl_cffi` com impersonação em nível de TLS e HTTP/2 do navegador **Google Chrome 124**.
   * Não requer aprovação em portais de desenvolvedores, contorna bloqueios de WAF / Cloudflare e funciona instantaneamente.
2. **Conector Oficial TOP Protocol:**
   * Caso você configure `ALIEXPRESS_APP_KEY` e `ALIEXPRESS_APP_SECRET` no seu arquivo `.env`, o sistema conecta na API oficial do AliExpress com assinatura criptográfica **HMAC-SHA256**.

---

## 🏷️ O "Modo Choice" (`--choice`)

O AliExpress subsidia o Imposto de Importação em produtos com o selo **AliExpress Choice** ou cupons especiais de remessa:
* **Sem a flag `--choice`:** O sistema aplica a regra geral do Remessa Conforme (20% de II até US$ 50 + ICMS por dentro).
* **Com a flag `--choice`:** O sistema zera a alíquota do Imposto de Importação ($II = R\$ 0,00$), cobrando exclusivamente o ICMS estadual.

---

## 🛡️ Pipeline de Filtros Inteligentes

### 1. Algoritmo Anti-Trick (Anti-Pegadinha)
Anúncios maliciosos frequentemente utilizam fotos de um smartwatch ou óculos completo com preço de R$ 5,00, quando na verdade estão vendendo apenas uma pulseira ou capa de proteção.
* O algoritmo analisa o título, descrição e proporção de preço em relação à média do nicho. Se detectar que é um acessório descontextualizado, o item é descartado automaticamente.

### 2. Dicionário Semântico Cruzado (PT $\leftrightarrow$ EN)
O sistema traduz e cruza sinônimos de especificações técnicas:
* `safira` $\leftrightarrow$ `sapphire`
* `aço` / `316l` $\leftrightarrow$ `stainless steel`
* `sem logo` / `estéril` $\leftrightarrow$ `sterile dial`
* `automático` $\leftrightarrow$ `nh35`, `miyota`

Você pode forçar termos obrigatórios com `--incluir` e banir termos com `--excluir`.

### 3. Filtros de Reputação e Volume
* `--min-nota 4.7`: Descarta vendedores com histórico duvidoso.
* `--min-vendas 50`: Exige prova de tração real de vendas.

---

## 💻 Exemplos de Execução na CLI

### Busca simples com cálculo de impostos:
```bash
python -m src.cli.main --busca "relogio automatico safira"
```

### Mineração com modo Choice, filtro de reputação e exportação em Excel:
```bash
python -m src.cli.main --busca "relogio nh35" --choice --min-nota 4.8 --min-vendas 20 --exportar
```

### Busca refinada com termos obrigatórios e proibidos:
```bash
python -m src.cli.main --busca "oculos quadrado" --incluir "uv400, polarizado" --excluir "criança, infantil" --margem 50
```
