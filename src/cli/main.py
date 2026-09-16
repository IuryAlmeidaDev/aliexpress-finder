import argparse
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import load_config
from src.clients.direct_scraper import DirectAliExpressClient
from src.clients.official_api import OfficialAliExpressClient
from src.clients.alibaba_scraper import DirectAlibabaClient
from src.filters.pipeline import FilterPipeline
from src.filters.alibaba_pipeline import AlibabaFilterPipeline
from src.finance.taxes import calculate_import_taxes
from src.finance.margins import simulate_resale
from src.finance.wholesale import calculate_wholesale_batch_costs, simulate_wholesale_resale
from src.cli.formatters import render_results_table, render_alibaba_table
from src.cli.exporter import export_to_excel
from src.mercado_livre.client import MercadoLivreClient
from src.mercado_livre.repository import RadarRepository
from src.mercado_livre.service import MercadoLivreRadar
from rich.console import Console

console = Console()

def run():
    parser = argparse.ArgumentParser(description="AliExpress Resale Opportunity Finder & Tax Calculator")
    parser.add_argument("--fonte", type=str, choices=["ali", "alibaba", "mercado-livre"], default="ali", help="Fonte: 'ali', 'alibaba' ou radar 'mercado-livre'")
    parser.add_argument("--busca", type=str, default="", help="Termo principal de busca (obrigatório para AliExpress/Alibaba)")
    parser.add_argument("--incluir", type=str, default="", help="Termos obrigatórios separados por vírgula (ex: 'safira, sem logo')")
    parser.add_argument("--excluir", type=str, default="", help="Termos proibidos separados por vírgula (ex: 'quartz, pulseira')")
    parser.add_argument("--max-custo", type=float, default=None, help="Custo final máximo em R$")
    parser.add_argument("--margem", type=float, default=40.0, help="Margem líquida desejada em porcentagem (padrão: 40%%)")
    parser.add_argument("--min-vendas", type=int, default=None, help="Vendas mínimas do produto (padrão: valor do .env)")
    parser.add_argument("--min-nota", type=float, default=None, help="Avaliação mínima da loja/produto (padrão: valor do .env)")
    parser.add_argument("--choice", action="store_true", help="Aplica subsídio Choice do AliExpress (Imposto de Importação zerado, apenas ICMS)")
    parser.add_argument("--max-moq", type=int, default=None, help="Quantidade mínima de pedido máxima permitida (apenas para Alibaba)")
    parser.add_argument("--verificados", action="store_true", help="Filtra apenas fornecedores verificados (Verified Supplier) no Alibaba")
    parser.add_argument("--trade-assurance", action="store_true", help="Filtra apenas fornecedores com Trade Assurance no Alibaba")
    parser.add_argument("--exportar", action="store_true", help="Salva os resultados em arquivo Excel")
    parser.add_argument("--ml-category", action="append", default=[], help="ID de categoria-folha do Mercado Livre; pode repetir")
    parser.add_argument("--ml-db", type=str, default="", help="Banco SQLite do radar Mercado Livre")
    parser.add_argument("--ml-report-dir", type=str, default="", help="Diretório dos relatórios do radar")
    parser.add_argument("--ml-max-categories", type=int, default=30, help="Máximo de categorias por rodada")
    parser.add_argument("--ml-max-candidates", type=int, default=100, help="Máximo de produtos enriquecidos")
    parser.add_argument("--ml-mode", choices=["manual", "weekly"], default="manual", help="Origem da execução do radar")
    args = parser.parse_args()

    cfg = load_config()

    if args.fonte == "mercado-livre":
        categories = args.ml_category or [
            value.strip() for value in cfg.MERCADO_LIVRE_CATEGORY_IDS.split(",") if value.strip()
        ]
        db_path = args.ml_db or cfg.MERCADO_LIVRE_DB_PATH
        report_dir = args.ml_report_dir or cfg.MERCADO_LIVRE_REPORT_DIR
        console.print("[bold cyan]Radar Mercado Livre:[/bold cyan] buscando demanda e potencial de marca própria...")
        with RadarRepository(db_path) as repository:
            radar = MercadoLivreRadar(
                client=MercadoLivreClient(
                    cfg.MERCADO_LIVRE_ACCESS_TOKEN,
                    cfg.MERCADO_LIVRE_SITE_ID,
                    client_id=cfg.MERCADO_LIVRE_CLIENT_ID,
                    client_secret=cfg.MERCADO_LIVRE_CLIENT_SECRET,
                    refresh_token=cfg.MERCADO_LIVRE_REFRESH_TOKEN,
                    token_file=cfg.MERCADO_LIVRE_TOKEN_FILE,
                ),
                repository=repository,
                report_dir=report_dir,
                max_categories=max(1, args.ml_max_categories),
                max_candidates=max(1, args.ml_max_candidates),
            )
            result = radar.run(mode=args.ml_mode, category_ids=categories or None)
        if result.status == "failed":
            console.print(f"[bold red]Falha no radar:[/bold red] {' | '.join(result.errors)}")
            sys.exit(1)
        color = "yellow" if result.status == "partial" else "green"
        console.print(
            f"[{color}]Coleta {result.status}: {result.products} produtos, "
            f"{result.opportunities} oportunidades prioritárias.[/{color}]"
        )
        if result.errors:
            console.print(f"[yellow]Cobertura parcial: {len(result.errors)} ocorrência(s).[/yellow]")
        console.print(f"[bold green]Relatório:[/bold green] {result.report_path}")
        return

    if not args.busca.strip():
        parser.error("--busca é obrigatório para as fontes 'ali' e 'alibaba'")

    target_margin = args.margem / 100.0
    if target_margin + cfg.DEFAULT_MARKETPLACE_FEE >= 1.0:
        console.print(
            f"[bold red]Erro:[/bold red] Margem desejada ({args.margem}%) somada à taxa do marketplace "
            f"({cfg.DEFAULT_MARKETPLACE_FEE * 100:.1f}%) deve ser menor que 100%."
        )
        sys.exit(1)

    if args.fonte == "alibaba":
        console.print(f"[bold cyan]🏭 Buscando no Alibaba.com (Atacado/B2B) por:[/bold cyan] '{args.busca}'...")
        client = DirectAlibabaClient(usd_rate=cfg.DEFAULT_USD_BRL)
        raw_items = client.search(args.busca, max_items=50)
        if not raw_items:
            console.print("[yellow]Nenhum produto retornado na busca preliminar ou limite atingido.[/yellow]")
            sys.exit(0)

        include_terms = [t.strip() for t in args.incluir.split(",") if t.strip()]
        exclude_terms = [t.strip() for t in args.excluir.split(",") if t.strip()]

        pipeline = AlibabaFilterPipeline(
            max_moq=args.max_moq,
            only_verified=args.verificados,
            only_trade_assurance=args.trade_assurance
        )
        filtered_items = pipeline.filter_products(raw_items, args.busca, include_terms, exclude_terms)

        records = []
        for item in filtered_items:
            costs = calculate_wholesale_batch_costs(
                unit_price_brl=item["price"],
                moq=item["moq"],
                icms_rate=cfg.DEFAULT_ICMS_RATE
            )

            if args.max_custo is not None and costs.unit_landed_cost_brl > args.max_custo:
                continue

            resale = simulate_wholesale_resale(
                batch_landed_cost_brl=costs.total_batch_landed_cost_brl,
                moq=item["moq"],
                target_margin_pct=target_margin,
                marketplace_fee_pct=cfg.DEFAULT_MARKETPLACE_FEE
            )

            records.append({
                "Produto": item["title"],
                "Fornecedor": item.get("supplier_name", ""),
                "MOQ": item["moq"],
                "Preço Unit. (R$)": item["price"],
                "Custo Unit. Final (R$)": costs.unit_landed_cost_brl,
                "Investimento Lote (R$)": costs.total_batch_landed_cost_brl,
                "Sugestão Venda (R$)": resale.unit_sale_price_brl,
                "Lucro Líquido Lote (R$)": resale.projected_net_profit_brl,
                "ROI (%)": resale.roi_pct,
                "Verified": item.get("is_verified", False),
                "Trade Assurance": item.get("has_trade_assurance", False),
                "Anos": item.get("years_in_business", 0),
                "Link": item.get("url", "")
            })

        records.sort(key=lambda r: r["Custo Unit. Final (R$)"])

        if not records:
            console.print("[yellow]Nenhum produto passou em todos os critérios e filtros de segurança.[/yellow]")
            sys.exit(0)

        render_alibaba_table(records)

        if args.exportar:
            path = export_to_excel(records, "oportunidades_alibaba.xlsx")
            console.print(f"[bold green]📊 Planilha salva com sucesso em:[/bold green] {path}")

        return

    min_sales = args.min_vendas if args.min_vendas is not None else cfg.MIN_SALES_COUNT
    min_rating = args.min_nota if args.min_nota is not None else cfg.MIN_STORE_RATING

    console.print(f"[bold green]🔎 Buscando no AliExpress por:[/bold green] '{args.busca}'...")
    if args.choice:
        console.print("[cyan]🏷️ Modo Choice ativado: Imposto de Importação subsidiado (R$ 0,00)[/cyan]")
    console.print(f"[dim]Critérios: Nota min={min_rating} | Vendas min={min_sales} | Margem desejada={args.margem}%[/dim]")

    # Choose client: official if keys are present, otherwise direct scraper
    client = OfficialAliExpressClient(cfg.ALIEXPRESS_APP_KEY, cfg.ALIEXPRESS_APP_SECRET)
    if not client.is_configured():
        client = DirectAliExpressClient()

    raw_items = client.search(args.busca, max_items=50)
    if not raw_items:
        console.print("[yellow]Nenhum produto retornado na busca preliminar ou limite atingido.[/yellow]")
        sys.exit(0)

    # Filter pipeline
    include_terms = [t.strip() for t in args.incluir.split(",") if t.strip()]
    exclude_terms = [t.strip() for t in args.excluir.split(",") if t.strip()]

    pipeline = FilterPipeline(min_rating=min_rating, min_sales=min_sales)
    filtered_items = pipeline.filter_products(raw_items, args.busca, include_terms, exclude_terms)

    records = []

    for item in filtered_items:
        tax_res = calculate_import_taxes(
            product_price_brl=item["price"],
            shipping_fee_brl=item.get("shipping", 0.0),
            usd_brl_rate=cfg.DEFAULT_USD_BRL,
            icms_rate=cfg.DEFAULT_ICMS_RATE,
            choice_subsidized=args.choice
        )

        if args.max_custo and tax_res.total_landed_cost_brl > args.max_custo:
            continue

        margin_res = simulate_resale(
            landed_cost_brl=tax_res.total_landed_cost_brl,
            target_margin_pct=target_margin,
            marketplace_fee_pct=cfg.DEFAULT_MARKETPLACE_FEE
        )

        records.append({
            "Produto": item["title"],
            "Preço Ali (R$)": item["price"],
            "Impostos BR (R$)": tax_res.total_taxes_brl,
            "Custo Final (R$)": tax_res.total_landed_cost_brl,
            "Sugestão Venda (R$)": margin_res.suggested_sale_price_brl,
            "Lucro Líquido (R$)": margin_res.net_profit_brl,
            "ROI (%)": margin_res.roi_pct,
            "Avaliação": item.get("rating", 0.0),
            "Link": item.get("url", "")
        })

    # Sort records by lowest landed cost
    records.sort(key=lambda r: r["Custo Final (R$)"])

    if not records:
        console.print("[yellow]Nenhum produto passou em todos os critérios e filtros de segurança.[/yellow]")
        sys.exit(0)

    render_results_table(records)

    if args.exportar:
        path = export_to_excel(records, "oportunidades_aliexpress.xlsx")
        console.print(f"[bold green]📊 Planilha salva com sucesso em:[/bold green] {path}")

if __name__ == "__main__":
    run()
