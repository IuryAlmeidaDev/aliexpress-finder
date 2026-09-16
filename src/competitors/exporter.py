import pandas as pd
from typing import List, Dict, Any
from src.competitors.models import MarketDossier

def export_dossier_markdown(dossier: MarketDossier, filepath: str) -> None:
    """Exports an executive dossier report in Markdown format."""
    target = dossier.target

    md_lines = [
        f"# Dossiê de Inteligência Competitiva e Benchmarking",
        f"",
        f"## 🎯 1. Raio-X do Produto Analisado",
        f"- **Produto:** {target.title}",
        f"- **Preço de Referência:** R$ {target.reference_price_brl:.2f}",
        f"- **Termo de Busca Limpo:** `{target.clean_query}`",
        f"- **Kits / Acessórios Detectados:** {', '.join(target.kit_items) if target.kit_items else 'Nenhum'}",
    ]
    if target.url:
        md_lines.append(f"- **Link Original:** [{target.url}]({target.url})")

    md_lines.extend([
        f"",
        f"---",
        f"",
        f"## ⚔️ 2. Mapeamento de Concorrentes Diretos",
        f"",
        f"| # | Concorrente | Loja / Plataforma | Preço (R$) | Envio | Kit / Brindes | Diferenciais | Link |",
        f"|---|---|---|---|---|---|---|---|",
    ])

    for idx, c in enumerate(dossier.competitors, start=1):
        kit_str = ", ".join(c.kit_items) if c.kit_items else "-"
        diff_str = ", ".join(c.differentials) if c.differentials else "-"
        md_lines.append(
            f"| {idx} | {c.title} | {c.store_name} ({c.platform}) | R$ {c.price_brl:.2f} | {c.shipping_type} | {kit_str} | {diff_str} | [Ver Oferta]({c.url}) |"
        )

    md_lines.extend([
        f"",
        f"---",
        f"",
        f"## 📊 3. Benchmarking de Mercado e Estatísticas",
        f"- **Menor Preço Encontrado:** R$ {dossier.min_competitor_price:.2f}",
        f"- **Preço Médio da Concorrência:** R$ {dossier.avg_competitor_price:.2f}",
        f"- **Maior Preço Encontrado:** R$ {dossier.max_competitor_price:.2f}",
        f"- **Preço Mediano:** R$ {dossier.median_competitor_price:.2f}",
        f"- **Participação de Envio Rápido (Full):** {dossier.full_shipping_share_pct}%",
        f"- **Acessórios Comuns:** {', '.join(dossier.common_kit_items) if dossier.common_kit_items else 'Nenhum'}",
        f"- **Teto de Custo FOB na China (p/ 35% de margem líquida):** US$ {dossier.target_fob_china_usd:.2f} (~R$ {dossier.target_fob_china_usd * 5.50:.2f})",
        f"",
        f"---",
        f"",
        f"## 💡 4. Brechas de Mercado e Estratégia de Diferenciação",
    ])

    for gap in dossier.market_gaps:
        md_lines.append(f"- {gap}")

    if dossier.recommended_china_suppliers:
        md_lines.extend([
            f"",
            f"---",
            f"",
            f"## 🏭 5. Fornecedores Recomendados na China (Alibaba / AliExpress)",
            f"",
            f"| Fabricante / Produto | Preço | MOQ | Link |",
            f"|---|---|---|---|",
        ])
        for s in dossier.recommended_china_suppliers:
            md_lines.append(
                f"| {s.get('title', '')} | {s.get('price', '')} | {s.get('moq', '-')} | [Acessar no Fornecedor]({s.get('url', '')}) |"
            )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

def export_competitors_excel(dossier: MarketDossier, filepath: str) -> None:
    """Exports competitor comparison data and market statistics to an Excel spreadsheet."""
    competitor_rows = []
    for idx, c in enumerate(dossier.competitors, start=1):
        competitor_rows.append({
            "Posição": idx,
            "Título do Anúncio": c.title,
            "Loja / Vendedor": c.store_name,
            "Plataforma": c.platform,
            "Preço de Venda (R$)": c.price_brl,
            "Tipo de Envio": c.shipping_type,
            "Avaliação (Nota)": c.rating if c.rating is not None else "",
            "Qtd. Avaliações": c.reviews_count if c.reviews_count is not None else "",
            "Kits / Brindes": ", ".join(c.kit_items),
            "Diferenciais": ", ".join(c.differentials),
            "Link da Oferta": c.url,
        })

    df_competitors = pd.DataFrame(competitor_rows)

    summary_rows = [
        {"Métrica / Estratégia": "Produto Analisado", "Valor": dossier.target.title},
        {"Métrica / Estratégia": "Preço de Referência", "Valor": f"R$ {dossier.target.reference_price_brl:.2f}"},
        {"Métrica / Estratégia": "Menor Preço Concorrência", "Valor": f"R$ {dossier.min_competitor_price:.2f}"},
        {"Métrica / Estratégia": "Preço Médio Concorrência", "Valor": f"R$ {dossier.avg_competitor_price:.2f}"},
        {"Métrica / Estratégia": "Maior Preço Concorrência", "Valor": f"R$ {dossier.max_competitor_price:.2f}"},
        {"Métrica / Estratégia": "Preço Mediano", "Valor": f"R$ {dossier.median_competitor_price:.2f}"},
        {"Métrica / Estratégia": "Participação Envio Full (%)", "Valor": f"{dossier.full_shipping_share_pct}%"},
        {"Métrica / Estratégia": "Kits Mais Frequentes", "Valor": ", ".join(dossier.common_kit_items)},
        {"Métrica / Estratégia": "Teto Custo FOB China (USD)", "Valor": f"US$ {dossier.target_fob_china_usd:.2f}"},
        {"Métrica / Estratégia": "Teto Custo FOB China (BRL)", "Valor": f"R$ {dossier.target_fob_china_usd * 5.50:.2f}"},
    ]
    for idx, gap in enumerate(dossier.market_gaps, start=1):
        summary_rows.append({"Métrica / Estratégia": f"Brecha de Mercado #{idx}", "Valor": gap})

    df_summary = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df_competitors.to_excel(writer, sheet_name="Concorrentes", index=False)
        df_summary.to_excel(writer, sheet_name="Resumo e Estratégia", index=False)
