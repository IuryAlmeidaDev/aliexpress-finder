# Especificação de Design: AliExpress Resale Finder & Tax Calculator

- **Data**: 2026-09-14
- **Status**: Aprovado para Planejamento
- **Projeto**: `aliexpress-finder`
- **Caminho**: `C:\Users\iuryc\projects\aliexpress-finder`

---

## 1. Visão Geral e Objetivos

O **AliExpress Resale Finder & Tax Calculator** é uma ferramenta de busca e inteligência comercial desenvolvida para empreendedores e revendedores no Brasil que importam produtos do AliExpress (como relógios automáticos, eletrônicos e acessórios de alta demanda).

### Principais Objetivos:
1. **Garimpo Preciso de Oportunidades**: Realizar buscas refinadas no AliExpress baseadas em termos livres e atributos técnicos específicos (ex: *"relógio automático com vidro de safira sem logo"*).
2. **Filtro Anti-Pegadinha**: Detectar e eliminar anúncios enganosos comuns onde o menor preço listado refere-se apenas a acessórios (pulseiras de borracha, caixas vazias ou ferramentas) em vez do produto principal.
3. **Filtro de Segurança e Confiabilidade**: Descartar produtos de lojas com reputação baixa (avaliação < 4.5 estrelas) ou poucas vendas, minimizando riscos de pós-venda.
4. **Cálculo Tributário Rigoroso (Brasil)**:
   - Aplicação exata das regras do programa **Remessa Conforme**:
     - Até US$ 50: 20% de Imposto de Importação (II) + ICMS (~17% a 20% calculado "por dentro").
     - Acima de US$ 50: 60% de II com dedução fixa de US$ 20 + ICMS por dentro.
   - Soma do frete internacional real para apuração do **Custo Final na Porta (Landed Cost em R$)**.
5. **Simulação de Margem de Lucro e Revenda**:
   - Projeção de preço de venda no mercado nacional (ex: Mercado Livre, Shopee ou venda direta).
   - Abatimento das comissões do marketplace (ex: 14% a 18%).
   - Apuração do Lucro Líquido Real (R$) e Margem de Retorno (ROI %).
6. **Interface Terminal (CLI) Simples & Exportador**:
   - Tabela rica no terminal com cores, links diretos e ordenação pelo menor custo ou maior margem.
   - Exportação opcional para planilha Excel/CSV para controle de estoque e cotações.
7. **Arquitetura Híbrida (Pronta para API Oficial)**:
   - Coletor direto/local para uso imediato sem depender de chaves externas.
   - Conector pronto para a API Oficial do AliExpress (`App Key` e `App Secret`) para ativação assim que o cadastro como Dropshipper/Afiliado for aprovado.

---

## 2. Arquitetura do Sistema

```
aliexpress-finder/
├── .env.example
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py             # Configurações de taxas, câmbio, margens e credenciais
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py    # Interface comum de busca
│   │   ├── direct_scraper.py # Coletor direto (Playwright / HTTP Stealth)
│   │   └── official_api.py   # Conector TOP Protocol (App Key / Secret)
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── anti_trick.py     # Filtro de acessórios e preços espúrios
│   │   ├── semantic.py       # Inclusão/exclusão de termos (safira, quartzo, réplicas)
│   │   └── reputation.py     # Nota mínima e volume de pedidos
│   ├── finance/
│   │   ├── __init__.py
│   │   ├── taxes.py          # Motor tributário (II + ICMS por dentro)
│   │   └── margins.py        # Simulação de preço de venda e margens
│   └── cli/
│       ├── __init__.py
│       ├── formatters.py     # Exibição de tabelas com Rich no terminal
│       └── exporter.py       # Geração de arquivos Excel (.xlsx) e CSV
└── tests/
    ├── test_taxes.py         # Testes dos cenários de importação (< $50 e > $50)
    ├── test_filters.py       # Testes dos filtros anti-pegadinha e semânticos
    └── test_margins.py       # Testes da simulação de lucro
```

---

## 3. Detalhamento dos Componentes

### 3.1. Motor Financeiro e Tributário (`src/finance/taxes.py`)
- **Entradas**:
  - `product_price_brl`: Preço do produto no AliExpress em Reais.
  - `shipping_fee_brl`: Frete internacional em Reais.
  - `usd_brl_rate`: Cotação do Dólar (obtida automaticamente via AwesomeAPI ou configurada no `.env`).
  - `icms_rate`: Alíquota de ICMS estadual padrão (padrão: 17%, ajustável no `.env` ou CLI).
- **Cálculo Tributário**:
  1. Converter Valor Aduaneiro para USD: $V_{USD} = \frac{\text{Preço} + \text{Frete}}{\text{Cotação USD}}$
  2. **Imposto de Importação (II)**:
     - Se $V_{USD} \le 50$: $II = 0.20 \times (\text{Preço} + \text{Frete})$
     - Se $V_{USD} > 50$: $II = [0.60 \times (\text{Preço} + \text{Frete})] - (20 \times \text{Cotação USD})$
  3. **Base de Cálculo do ICMS ("por dentro")**:
     $$\text{Base ICMS} = \frac{\text{Preço} + \text{Frete} + II}{1 - \text{ICMS}}$$
     $$\text{Valor ICMS} = \text{Base ICMS} \times \text{ICMS}$$
  4. **Custo Final (Landed Cost)**:
     $$\text{Custo Final} = \text{Preço} + \text{Frete} + II + \text{Valor ICMS}$$

### 3.2. Simulador de Margem (`src/finance/margins.py`)
- Parâmetros:
  - `target_margin_pct` (ex: 40%): Margem líquida desejada sobre o preço de venda.
  - `marketplace_fee_pct` (ex: 16%): Taxa de comissão do canal de venda (ex: Mercado Livre Clássico/Premium ou Shopee).
- Saída:
  - **Preço de Venda Sugerido**: Preço que cobre o custo final, a comissão do marketplace e entrega a margem líquida desejada.
  - **Lucro Líquido em R$**: Ganho real após todos os custos e taxas.
  - **ROI (%)**: $\frac{\text{Lucro Líquido}}{\text{Custo Final}} \times 100$.

### 3.3. Filtros Inteligentes (`src/filters/`)
- **`anti_trick.py`**:
  - Detecta palavras-chave de partes ou acessórios avulsos (ex: *"strap"*, *"bracelet"*, *"bezel"*, *"box only"*, *"ferramenta"*, *"pulseira"* quando a busca principal é por *"relógio"*).
  - Descarta variações cujo valor esteja anormalmente abaixo da mediana do nicho (preços discrepantes indicativos de acessórios).
- **`semantic.py`**:
  - **Termos obrigatórios (Must Have)**: Valida que especificações solicitadas pelo usuário (ex: *safira*, *safir*, *sapphire*, *sterile*, *sem logo*) estão presentes no título ou atributos.
  - **Termos negativos (Exclude)**: Descarta produtos contendo palavras indesejadas (ex: *quartz*, *quartzo*, *bateria* em buscas de relógios automáticos).
- **`reputation.py`**:
  - Filtra por nota mínima de avaliação do produto (padrão: $\ge 4.5$ estrelas).
  - Filtra por volume mínimo de vendas (padrão: $\ge 10$ unidades vendidas).

### 3.4. Coletor e Conectores (`src/clients/`)
- **Modo Coletor Direto (`direct_scraper.py`)**:
  - Realiza requisições HTTPS simulando cabeçalhos de navegador com parâmetros regionais (Brasil, moeda BRL, frete BR).
  - Extrai dados estruturados dos produtos (ID, título, preço atual, preço original, frete, avaliação, total de vendas, imagem e link de compra).
- **Modo API Oficial (`official_api.py`)**:
  - Implementa a assinatura HMAC-SHA256 TOP Protocol para chamar o endpoint oficial `aliexpress.affiliate.product.query` ou as APIs de dropshipping quando as chaves forem liberadas.

### 3.5. Interface de Linha de Comando (`src/cli/`)
- Permite uso interativo ou via flags:
  ```bash
  python -m src.cli.main --busca "relogio automatico" --incluir "safira, sem logo" --excluir "quartz, pulseira" --max-custo 300 --margem 45 --exportar
  ```
- Exibe tabela formatada e colorida via biblioteca `rich`:
  - Nome do Produto (com link direto)
  - Preço no AliExpress
  - Imposto Estimado (II + ICMS)
  - Custo Final na Porta (R$)
  - Preço Sugerido de Revenda (R$)
  - Lucro Líquido Estimado (R$)
  - Avaliação / Vendas

---

## 4. Plano de Testes e Validação
1. **Testes Unitários de Tributação (`test_taxes.py`)**:
   - Caso 1: Produto de R$ 100 com frete de R$ 20 (Valor total < US$ 50). Validar cálculo de 20% II e ICMS 17% por dentro.
   - Caso 2: Produto de R$ 400 com frete grátis (Valor total > US$ 50). Validar alíquota de 60% com abatimento de US$ 20 e ICMS 17% por dentro.
2. **Testes Unitários de Filtros (`test_filters.py`)**:
   - Validar que anúncios de "pulseira" são filtrados em busca de "relógio".
   - Validar que termos como "quartz" são devidamente descartados.
3. **Teste de Execução do CLI**:
   - Validar comando de busca real, formatação de saída e exportação para Excel.
