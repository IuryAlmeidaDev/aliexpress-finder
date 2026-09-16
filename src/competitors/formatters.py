from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from src.competitors.models import MarketDossier

def print_competitor_dossier_terminal(dossier: MarketDossier, console: Console = None) -> None:
    """Prints a beautiful, executive-ready terminal report using Rich."""
    if console is None:
        console = Console()

    target = dossier.target

    # 1. Target Product Panel
    target_info = (
        f"[bold cyan]Produto de Referência:[/bold cyan] {target.title}\n"
        f"[bold cyan]Preço de Referência:[/bold cyan] R$ {target.reference_price_brl:.2f}\n"
        f"[bold cyan]Busca Otimizada:[/bold cyan] '{target.clean_query}'\n"
        f"[bold cyan]Kits / Brindes Detectados:[/bold cyan] {', '.join(target.kit_items) if target.kit_items else 'Nenhum'}"
    )
    if target.url:
        target_info += f"\n[bold cyan]Link Original:[/bold cyan] {target.url}"

    console.print(Panel(target_info, title="🎯 [bold green]RAIO-X DO PRODUTO ANALISADO[/bold green]", expand=False))

    # 2. Competitors Table
    table = Table(
        title="⚔️ [bold yellow]TOP CONCORRENTES DIRETOS NO BRASIL[/bold yellow]",
        show_header=True,
        header_style="bold magenta",
        expand=True
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Produto Concorrente", style="bold white", ratio=3)
    table.add_column("Loja / Plataforma", style="cyan", ratio=2)
    table.add_column("Preço (R$)", style="green", justify="right")
    table.add_column("Envio", style="yellow", justify="center")
    table.add_column("Kit / Acessórios", style="blue")
    table.add_column("Diferenciais", style="magenta")

    for idx, c in enumerate(dossier.competitors, start=1):
        shipping_badge = f"[bold green]{c.shipping_type}[/bold green]" if c.shipping_type == "Full" else c.shipping_type
        kit_str = ", ".join(c.kit_items) if c.kit_items else "[dim]Sem kit[/dim]"
        diff_str = ", ".join(c.differentials) if c.differentials else "-"
        
        table.add_row(
            str(idx),
            c.title[:55] + ("..." if len(c.title) > 55 else ""),
            f"{c.store_name}\n[dim]{c.platform}[/dim]",
            f"R$ {c.price_brl:.2f}",
            shipping_badge,
            kit_str,
            diff_str
        )

    console.print(table)

    # 3. Market Benchmarking KPIs Panel
    stats_info = (
        f"📊 [bold]Menor Preço Concorrência:[/bold] R$ {dossier.min_competitor_price:.2f}  |  "
        f"[bold]Preço Médio:[/bold] [bold green]R$ {dossier.avg_competitor_price:.2f}[/bold green]  |  "
        f"[bold]Maior Preço:[/bold] R$ {dossier.max_competitor_price:.2f}\n"
        f"🚚 [bold]Presença em Envio Rápido (Full):[/bold] {dossier.full_shipping_share_pct}%\n"
        f"🎁 [bold]Acessórios Comuns no Mercado:[/bold] {', '.join(dossier.common_kit_items) if dossier.common_kit_items else 'Nenhum padrão identificado'}\n"
        f"🇨🇳 [bold yellow]Teto de Custo FOB na China (p/ 35% margem):[/bold yellow] [bold green]US$ {dossier.target_fob_china_usd:.2f}[/bold green] (R$ {dossier.target_fob_china_brl:.2f})"
    )
    console.print(Panel(stats_info, title="📈 [bold cyan]ESTATÍSTICAS E BENCHMARKING DE PREÇO[/bold cyan]", expand=False))

    # 4. Market Gaps & Actionable Insights
    if dossier.market_gaps:
        gaps_text = "\n".join([f"• {gap}" for gap in dossier.market_gaps])
        console.print(Panel(gaps_text, title="💡 [bold yellow]BRECHAS DE MERCADO E OPORTUNIDADES[/bold yellow]", expand=False))

    # 5. China Suppliers if available
    if dossier.recommended_china_suppliers:
        sup_table = Table(
            title="🏭 [bold green]FORNECEDORES RECOMENDADOS NA CHINA (ALIBABA / ALIEXPRESS)[/bold green]",
            show_header=True,
            header_style="bold green",
            expand=True
        )
        sup_table.add_column("Fabricante / Produto", style="bold white")
        sup_table.add_column("Preço Unitário", style="green", justify="right")
        sup_table.add_column("MOQ", style="cyan", justify="center")
        sup_table.add_column("Link", style="blue")

        for s in dossier.recommended_china_suppliers:
            sup_table.add_row(
                str(s.get("title", ""))[:60],
                str(s.get("price", "")),
                str(s.get("moq", "-")),
                str(s.get("url", ""))
            )
        console.print(sup_table)
