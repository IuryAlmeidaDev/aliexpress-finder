from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

def render_results_table(records: List[Dict[str, Any]]):
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
