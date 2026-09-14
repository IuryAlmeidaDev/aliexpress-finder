from dataclasses import dataclass

@dataclass
class MarginSimulationResult:
    landed_cost_brl: float
    suggested_sale_price_brl: float
    marketplace_fee_pct: float
    marketplace_fee_brl: float
    net_revenue_brl: float
    net_profit_brl: float
    net_margin_pct: float
    roi_pct: float

def simulate_resale(
    landed_cost_brl: float,
    target_margin_pct: float = 0.40,
    marketplace_fee_pct: float = 0.16
) -> MarginSimulationResult:
    """
    Simulates resale price, fees, net profit and ROI.
    Formula:
    Sale Price = Landed Cost / (1 - marketplace_fee_pct - target_margin_pct)
    """
    if landed_cost_brl < 0:
        raise ValueError("landed_cost_brl cannot be negative")
    denominator = 1.0 - marketplace_fee_pct - target_margin_pct
    if denominator <= 0:
        raise ValueError("Sum of marketplace fee and target margin must be less than 100%")

    suggested_sale_price = round(landed_cost_brl / denominator, 2)
    marketplace_fee = round(suggested_sale_price * marketplace_fee_pct, 2)
    net_revenue = round(suggested_sale_price - marketplace_fee, 2)
    net_profit = round(net_revenue - landed_cost_brl, 2)
    roi_pct = round((net_profit / landed_cost_brl) * 100.0, 2) if landed_cost_brl > 0 else 0.0
    actual_margin_pct = round(net_profit / suggested_sale_price, 2) if suggested_sale_price > 0 else 0.0

    return MarginSimulationResult(
        landed_cost_brl=landed_cost_brl,
        suggested_sale_price_brl=suggested_sale_price,
        marketplace_fee_pct=marketplace_fee_pct,
        marketplace_fee_brl=marketplace_fee,
        net_revenue_brl=net_revenue,
        net_profit_brl=net_profit,
        net_margin_pct=actual_margin_pct,
        roi_pct=roi_pct,
    )
