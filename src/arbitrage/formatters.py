from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from src.arbitrage.models import ArbitrageReport

def print_arbitrage_report_terminal(report: ArbitrageReport, console: Console = None) -> None:
    if console is None:
        console = Console()

    # Executive Summary Panel
    summary_text = (
        f"[bold]Nicho / Termo:[/bold] [cyan]{report.query}[/cyan] | "
        f"[bold]Fonte:[/bold] [yellow]{report.source}[/yellow] | "
        f"[bold]Câmbio:[/bold] R$ {report.usd_rate:.2f}\n"
        f"📊 [bold]Total Analisado:[/bold] {report.total_scanned} produtos\n\n"
        f"  🌟 [bold green]Oceano Azul (Pioneirismo):[/bold green] {report.blue_ocean_count} itens\n"
        f"  🚀 [bold blue]Alta Margem (Arbitragem):[/bold blue] {report.high_margin_count} itens\n"
        f"  💎 [bold magenta]Marca Própria (Diferenciação):[/bold magenta] {report.private_label_count} itens\n"
        f"  ⚠️ [bold yellow]Saturado (Guerra de Preço):[/bold yellow] {report.saturated_count} itens"
    )

    console.print(Panel(summary_text, title="[bold green]Radar de Arbitragem: China Wholesale × Mercado Livre[/bold green]", border_style="green"))

    if not report.items:
        console.print("[yellow]Nenhum produto encontrado ou compatível com os filtros informados.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold white on dark_green", expand=True)
    table.add_column("Estratégia", style="bold", width=16)
    table.add_column("Produto (China)", width=32)
    table.add_column("FOB China", justify="right", width=12)
    table.add_column("Custo BR (c/ Imp)", justify="right", width=14)
    table.add_column("Preço ML", justify="right", width=12)
    table.add_column("Margem Liq.", justify="right", width=14)
    table.add_column("Concorrência ML", justify="center", width=15)

    for item in report.items:
        # Style strategy
        if item.strategy == "OCEANO_AZUL":
            strat_display = "[green]★ OCEANO AZUL[/green]"
        elif item.strategy == "ALTA_MARGEM":
            strat_display = "[blue]🚀 ALTA MARGEM[/blue]"
        elif item.strategy == "MARCA_PROPRIA":
            strat_display = "[magenta]💎 MARCA PRÓP.[/magenta]"
        else:
            strat_display = "[dim red]⚠️ SATURADO[/dim red]"

        # Sizing and titles
        title_display = f"[bold]{item.china_title[:45]}[/bold]..." if len(item.china_title) > 45 else item.china_title
        if item.moq > 1:
            title_display += f"\n[dim]MOQ: {item.moq} un | {item.supplier_name[:20]}[/dim]"

        fob_display = f"US$ {item.china_fob_usd:.2f}\n[dim]R$ {item.china_fob_brl:.2f}[/dim]"
        landed_display = f"R$ {item.landed_cost_unit_brl:.2f}"

        if item.ml_competitors_count > 0:
            price_display = f"R$ {item.reference_sale_price_brl:.2f}"
            comp_display = f"{item.ml_competitors_count} concorrentes\n[dim]{item.ml_full_share_pct:.0f}% Full[/dim]"
        else:
            price_display = f"[dim]Sugerido:[/dim]\nR$ {item.reference_sale_price_brl:.2f}"
            comp_display = "[green]0 concorrentes[/green]\n[dim]Sem concorrência[/dim]"

        margin_color = "green" if item.net_margin_pct >= 35 else ("blue" if item.net_margin_pct >= 20 else "red")
        margin_display = f"[{margin_color}][bold]{item.net_margin_pct:.1f}%[/bold]\n(R$ {item.net_profit_brl:.2f})[/{margin_color}]"

        table.add_row(
            strat_display,
            title_display,
            fob_display,
            landed_display,
            price_display,
            margin_display,
            comp_display
        )

    console.print(table)
