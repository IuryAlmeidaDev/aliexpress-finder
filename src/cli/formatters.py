import sys
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

def render_results_table(records: List[Dict[str, Any]]):
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    console = Console()
    table = Table(title="💎 Melhores Oportunidades Encontradas no AliExpress (Custo Brasil & Margem)", show_header=True, header_style="bold magenta")

    table.add_column("Produto", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Preço Ali", justify="right", style="white")
    table.add_column("Impostos", justify="right", style="yellow")
    table.add_column("Custo Final", justify="right", style="bold red")
    table.add_column("Sugestão Venda", justify="right", style="bold green")
    table.add_column("Lucro Líquido", justify="right", style="bold green")
    table.add_column("ROI", justify="right", style="bold blue")
    table.add_column("Aval.", justify="center", style="yellow")
    table.add_column("Link", style="blue")

    for r in records:
        table.add_row(
            r["Produto"][:38] + "..." if len(r["Produto"]) > 40 else r["Produto"],
            f"R$ {r['Preço Ali (R$)']:.2f}",
            f"R$ {r['Impostos BR (R$)']:.2f}",
            f"R$ {r['Custo Final (R$)']:.2f}",
            f"R$ {r['Sugestão Venda (R$)']:.2f}",
            f"R$ {r['Lucro Líquido (R$)']:.2f}",
            f"{r['ROI (%)']:.1f}%",
            f"{r.get('Avaliação', 0.0):.1f}⭐",
            f"[link={r['Link']}]Abrir[/link]"
        )

    console.print(table)

def render_alibaba_table(records: List[Dict[str, Any]]):
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    console = Console()
    table = Table(
        title="🏭 Oportunidades Atacado Alibaba.com (Fábrica & Custo de Lote)",
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Produto / Fornecedor", style="white", overflow="fold", max_width=35)
    table.add_column("MOQ", justify="center", style="bold yellow")
    table.add_column("Preço Unit. (R$)", justify="right", style="cyan")
    table.add_column("Custo Unit. Final", justify="right", style="magenta")
    table.add_column("Lote Total (R$)", justify="right", style="bold red")
    table.add_column("Sugestão Venda Un.", justify="right", style="green")
    table.add_column("Lucro Lote (R$)", justify="right", style="bold green")
    table.add_column("ROI (%)", justify="right", style="bold")
    table.add_column("Selos", justify="center")
    table.add_column("Link", justify="center")

    for r in records:
        url = r.get("Link", "")
        link_str = f"[link={url}]Abrir[/link]" if url else "-"
        badges = []
        if r.get("Verified"):
            badges.append("🛡️Verif")
        if r.get("Trade Assurance"):
            badges.append("🤝TA")
        if r.get("Anos"):
            badges.append(f"{r['Anos']}a")
        badges_str = " ".join(badges) if badges else "-"

        table.add_row(
            f"{r['Produto']}\n[dim]{r.get('Fornecedor', '')}[/dim]",
            f"{r['MOQ']} un",
            f"R$ {r['Preço Unit. (R$)']:.2f}",
            f"R$ {r['Custo Unit. Final (R$)']:.2f}",
            f"R$ {r['Investimento Lote (R$)']:.2f}",
            f"R$ {r['Sugestão Venda (R$)']:.2f}",
            f"R$ {r['Lucro Líquido Lote (R$)']:.2f}",
            f"{r['ROI (%)']:.1f}%",
            badges_str,
            link_str
        )

    console.print(table)
