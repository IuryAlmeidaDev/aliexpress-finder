---
id: radar-mercado-livre
title: Radar de Demanda (Mercado Livre)
sidebar_position: 5
---

# Radar de Demanda (Mercado Livre)

O **Radar Mercado Livre** analisa a ponta consumidora no Brasil para identificar produtos com alto volume de busca, demanda aquecida e potencial de substituição por produtos importados de marca própria (*Private Label*).

---

## 🎯 Objetivo da Funcionalidade

Enquanto os módulos do AliExpress e Alibaba olham para a **oferta** (o que as fábricas estão vendendo), o Radar do Mercado Livre olha para a **demanda** (o que o público brasileiro está comprando ativamente).

Ele responde a perguntas como:
* *Quais categorias de moda, acessórios ou eletrônicos estão vendendo mais de 5.000 unidades/mês?*
* *Onde os concorrentes estão vendendo produtos sem marca que você pode importar da China com embalagem própria e roubar a fatia de mercado?*

---

## 🗄️ Persistência e Inteligência em SQLite

O radar armazena os dados coletados em um banco de dados local SQLite (`data/mercado_livre_radar.db`):
* **Histórico de Tendências:** Rastreia o crescimento ou queda de volume de vendas de categorias específicas ao longo das semanas.
* **Score de Oportunidade:** Algoritmo ponderado que cruza preço de venda, densidade de concorrentes e volume estimado.
* **Geração de Relatórios:** Produz relatórios analíticos formatados na pasta `reports/`.

---

## 💻 Execução na CLI

### Executar a varredura do radar:
```bash
python -m src.cli.main --fonte mercado-livre
```

### Configurações avançadas via CLI:
* `--ml-category <ID>`: Força a análise de uma categoria específica (ex: `--ml-category MLB1430`).
* `--ml-max-categories <NUM>`: Limita a quantidade de categorias analisadas por rodada (padrão: 30).
* `--ml-max-candidates <NUM>`: Quantidade máxima de produtos enriquecidos com métricas avançadas (padrão: 100).
* `--ml-mode weekly`: Executa no modo de rotina semanal para atualizar o histórico do banco de dados.
