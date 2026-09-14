from dataclasses import dataclass

@dataclass
class WholesaleBatchResult:
    fob_batch_brl: float
    import_tax_batch_brl: float
    icms_batch_brl: float
    total_batch_landed_cost_brl: float
    unit_landed_cost_brl: float

@dataclass
class WholesaleResaleResult:
    unit_sale_price_brl: float
    projected_revenue_brl: float
    projected_net_profit_brl: float
    roi_pct: float

def calculate_wholesale_batch_costs(
    unit_price_brl: float,
    moq: int,
    icms_rate: float = 0.17,
    import_tax_rate: float = 0.60
) -> WholesaleBatchResult:
    if moq < 1:
        moq = 1
    fob_batch = unit_price_brl * moq
    import_tax = fob_batch * import_tax_rate

    # ICMS "por dentro": Base = (fob + II) / (1 - icms_rate)
    grossed_base = (fob_batch + import_tax) / (1.0 - icms_rate)
    icms = grossed_base * icms_rate

    total_batch_landed_cost = fob_batch + import_tax + icms
    unit_landed_cost = total_batch_landed_cost / moq

    return WholesaleBatchResult(
        fob_batch_brl=round(fob_batch, 2),
        import_tax_batch_brl=round(import_tax, 2),
        icms_batch_brl=round(icms, 2),
        total_batch_landed_cost_brl=round(total_batch_landed_cost, 2),
        unit_landed_cost_brl=round(unit_landed_cost, 2),
    )

def simulate_wholesale_resale(
    batch_landed_cost_brl: float,
    moq: int,
    target_margin_pct: float = 0.40,
    marketplace_fee_pct: float = 0.16
) -> WholesaleResaleResult:
    if moq < 1:
        moq = 1
    if target_margin_pct + marketplace_fee_pct >= 1.0:
        raise ValueError("Sum of margin and marketplace fee must be strictly less than 1.0 (100%)")

    unit_landed_cost = batch_landed_cost_brl / moq
    denominator = 1.0 - marketplace_fee_pct - target_margin_pct
    unit_sale_price = unit_landed_cost / denominator

    projected_revenue = unit_sale_price * moq
    fee_total = projected_revenue * marketplace_fee_pct
    projected_net_profit = projected_revenue - fee_total - batch_landed_cost_brl
    roi_pct = (projected_net_profit / batch_landed_cost_brl) * 100.0 if batch_landed_cost_brl > 0 else 0.0

    return WholesaleResaleResult(
        unit_sale_price_brl=round(unit_sale_price, 2),
        projected_revenue_brl=round(projected_revenue, 2),
        projected_net_profit_brl=round(projected_net_profit, 2),
        roi_pct=round(roi_pct, 1),
    )
