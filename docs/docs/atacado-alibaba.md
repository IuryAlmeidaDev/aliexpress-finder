---
id: atacado-alibaba
title: Atacado no Alibaba (B2B)
sidebar_position: 4
---

# Atacado no Alibaba (Importação B2B)

O módulo do **Alibaba** destina-se a empreendedores e lojistas que buscam **escala comercial**, negociando diretamente com fábricas chinesas sob o regime formal de atacado e private label.

---

## 🏭 Características da Operação B2B

Diferente do AliExpress (onde o foco é a compra unitária), o Alibaba trabalha com lógica industrial:
1. **Quantidade Mínima de Pedido (MOQ):** Fábricas exigem lotes mínimos (ex: 20, 100, 500 ou 1.000 unidades) para produzir ou aplicar a sua marca própria.
2. **Faixas de Preço por Escala:** Quanto maior o lote, menor o preço unitário FOB (*Free On Board*).
3. **Regime Tributário de Atacado (RTS):** No atacado formal, aplica-se a alíquota cheia de **60% de Imposto de Importação (II)** sobre o valor aduaneiro + **ICMS estadual calculado por dentro** (sem as isenções do Remessa Conforme).

---

## 🛡️ Filtros de Segurança Fabril

Para evitar intermediários desqualificados (*traders*) e proteger o capital do importador, o módulo possui filtros rígidos:

* **`--verificados` (*Verified Supplier*):**
  * Restringe os resultados a fábricas que passaram por auditoria física presencial de empresas certificadoras independentes internacionais (como TÜV Rheinland, SGS ou Bureau Veritas).
* **`--trade-assurance`:**
  * Garante que o pagamento fique retido em custódia no Alibaba até a confirmação de embarque e conformidade do lote, com direito a reembolso total em caso de não conformidade ou atraso.
* **`--max-moq <QTD>`:**
  * Teto máximo de pedido mínimo. Essencial para quem está começando e não quer ver fábricas exigindo pedidos de 10.000 peças.

---

## 📊 Simulação Financeira por Lote Fechado

Para cada produto encontrado, o motor calcula:
* **Investimento Total do Lote (R$):** Custo de fábrica $\times$ MOQ + Impostos de Importação (60%) + ICMS por dentro.
* **Custo Unitário Desembarcado (R$):** Custo real de cada unidade colocada no seu estoque no Brasil.
* **Sugestão de Venda no Brasil (R$):** Preço mínimo de venda para garantir a margem líquida desejada após pagar a comissão do marketplace.
* **Lucro Líquido Projetado do Lote (R$):** Lucro total após a venda de 100% do lote.
* **Retorno sobre o Investimento (ROI %):** Ganho percentual sobre o capital total imobilizado no lote.

---

## 💻 Exemplos de Execução na CLI

### Busca de atacado com filtro de segurança e limite de MOQ:
```bash
python -m src.cli.main --fonte alibaba --busca "square sunglasses UV400" --max-moq 100 --verificados --trade-assurance
```

### Prospecção de relógios para marca própria com exportação:
```bash
python -m src.cli.main --fonte alibaba --busca "automatic watch sapphire" --max-moq 50 --verificados --margem 45 --exportar
```
*Gera o arquivo `oportunidades_alibaba.xlsx` com colunas de MOQ, tempo de fábrica, selos de segurança e simulação financeira completa.*
