---
id: motor-tributario-financeiro
title: Motor Tributário e Financeiro 🇧🇷
sidebar_position: 7
---

# Motor Tributário e Financeiro 🇧🇷

O motor de cálculo do **AliExpress & Alibaba Finder** foi modelado com precisão cirúrgica para reproduzir a legislação tributária aduaneira brasileira e as regras financeiras de e-commerce.

---

## 🏛️ 1. As Regras de Tributação Aduaneira

### A. Varejo Internacional (AliExpress B2C — Remessa Conforme)

Aprovado pela Lei nº 14.902/2024, o programa Remessa Conforme segue a seguinte estrutura de **Imposto de Importação (II)**:

* **Para compras até US$ 50,00:**
  ```text
  II = 20% × Valor Aduaneiro (Produto + Frete)
  ```
* **Para compras acima de US$ 50,00:**
  ```text
  II = max(0, 60% × Valor Aduaneiro - Dedução de US$ 20,00)
  ```
* **Modo Choice Subsidia (Flag `--choice`):**
  Quando o AliExpress subsidia o imposto aduaneiro no checkout, o Imposto de Importação é zerado:
  ```text
  II = R$ 0,00
  ```

---

### B. Atacado Industrial (Alibaba B2B — Regime de Tributação Simplificada)

Para compras comerciais de lote direto de fabricantes:
* Não se aplica o teto de isenção de US$ 50.
* Aplica-se a alíquota cheia de **60% de Imposto de Importação** sobre o total da fatura comercial (FOB + Frete).

---

## 🧮 2. O Cálculo do ICMS Estadual "Por Dentro"

No Brasil, o ICMS sobre importações é calculado pelo método do **gross-up (cálculo por dentro)**, onde o próprio imposto compõe sua base de cálculo.

### A Fórmula Matemática:
1. **Base de Cálculo do ICMS:**
   ```text
   Base ICMS = (Valor Aduaneiro + Imposto de Importação) / (1 - Alíquota ICMS)
   ```
2. **Valor a Pagar de ICMS:**
   ```text
   Valor ICMS = Base ICMS × Alíquota ICMS
   ```

### Exemplo Prático (Produto de R$ 100 com 20% II e 17% ICMS):
* Valor Aduaneiro: R$ 100,00
* Imposto de Importação (20%): R$ 20,00
* Soma inicial: R$ 120,00
* Base do ICMS (R$ 120 / (1 - 0,17)): **R$ 144,58**
* Valor do ICMS (R$ 144,58 × 17%): **R$ 24,58**
* **Custo Total Desembarcado:** R$ 100 + R$ 20 + R$ 24,58 = **R$ 144,58** *(e não R$ 137 como cálculos ingênuos assumem)*.

---

## 📈 3. Simulação de Margem Líquida e ROI

Para definir o preço de venda e avaliar o lucro real, o sistema desconta todas as pontas da cadeia:

```text
Preço de Venda Sugerido = Custo Desembarcado / (1 - Comissão Marketplace - Margem Líquida Alvo)
```

* **Comissão do Marketplace:** Padrão de 16% (Mercado Livre Premium / Shopee).
* **Taxa Fixa para Produtos de Baixo Valor:** O Mercado Livre cobra taxa fixa de aproximadamente R$ 6,00 para itens vendidos abaixo de R$ 79,00.
* **Margem Líquida (%):** Lucro líquido dividido pelo preço total de venda.
* **ROI (%):** Lucro líquido dividido pelo capital total investido no lote/produto.

---

## 💵 4. Câmbio Comercial em Tempo Real (AwesomeAPI)

A cotação do dólar oscila constantemente e afeta diretamente:
1. **O teto de US$ 50 da Remessa Conforme:** Se o dólar sobe, o teto em reais sobe; se desce, produtos próximos à fronteira de R$ 260–280 podem ser tributados a 60% em vez de 20%.
2. **O custo do lote no Alibaba (B2B):** Cotações FOB em dólar sofrem impacto proporcional em reais no valor final da fatura comercial.

### Como o Sistema Resolve o Câmbio Automaticamente:
* **API em Tempo Real:** Consulta a API pública da *AwesomeAPI* (`https://economia.awesomeapi.com.br/last/USD-BRL`), sem necessidade de chaves de API nem cadastros.
* **Cache Inteligente com TTL:** As cotações são armazenadas em `data/currency_cache.json` com validade de 2 horas. As consultas subsequentes são instantâneas (< 1ms).
* **Resiliência Offline:** Se a internet falhar ou a API estiver fora do ar, o sistema recorre ao cache local anterior ou ao valor padrão do `.env` (`DEFAULT_USD_BRL`), sem nunca travar a CLI.
* **Simulação Manual (`--usd <valor>`):** Para simular cenários de estresse ou volatilidade (ex: dólar a R$ 6,00), basta informar o parâmetro na linha de comando:
  ```bash
  python -m src.cli.main --busca "relogio safira" --usd 6.00
  ```

