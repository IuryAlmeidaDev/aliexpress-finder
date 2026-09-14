import pytest
from src.finance.wholesale import calculate_wholesale_batch_costs, simulate_wholesale_resale

def test_calculate_wholesale_batch_costs():
    # Unit price R$ 10, MOQ 50 => FOB = R$ 500
    # II 60% = R$ 300 => Base before ICMS = R$ 800
    # ICMS 17% por dentro => 800 / (1 - 0.17) * 0.17 = 963.86 * 0.17 = 163.86
    # Total batch landed cost = 800 + 163.86 = 963.86
    # Unit landed cost = 963.86 / 50 = 19.28
    res = calculate_wholesale_batch_costs(unit_price_brl=10.0, moq=50, icms_rate=0.17, import_tax_rate=0.60)
    assert res.fob_batch_brl == 500.0
    assert res.import_tax_batch_brl == 300.0
    assert round(res.icms_batch_brl, 2) == 163.86
    assert round(res.total_batch_landed_cost_brl, 2) == 963.86
    assert round(res.unit_landed_cost_brl, 2) == 19.28

def test_simulate_wholesale_resale():
    # Total batch landed cost = R$ 963.86, MOQ = 50, Unit landed cost = 19.2772 (or 19.277 in 3-dec scratchpad)
    # Suggested retail price per unit with 40% margin and 16% fee:
    # 19.277 / (1 - 0.16 - 0.40) = 19.277 / 0.44 = 43.81
    # Projected batch revenue: 963.86 / 0.44 = 2190.59 (or 2190.57 with 19.277 scratchpad)
    # Marketplace fee: 2190.59 * 0.16 = 350.49
    # Net profit: 2190.59 - 350.49 - 963.86 = 876.24 (or 876.22 with 19.277 scratchpad)
    # ROI: (876.24 / 963.86) * 100 = 90.9%
    batch_res = calculate_wholesale_batch_costs(unit_price_brl=10.0, moq=50)
    resale = simulate_wholesale_resale(
        batch_landed_cost_brl=batch_res.total_batch_landed_cost_brl,
        moq=50,
        target_margin_pct=0.40,
        marketplace_fee_pct=0.16
    )
    assert round(resale.unit_sale_price_brl, 2) == 43.81
    assert round(resale.projected_revenue_brl, 2) in (2190.57, 2190.59)
    assert round(resale.projected_net_profit_brl, 2) in (876.22, 876.24)
    assert round(resale.roi_pct, 1) == 90.9

def test_wholesale_batch_costs_min_moq():
    # MOQ < 1 falls back to 1
    res = calculate_wholesale_batch_costs(unit_price_brl=20.0, moq=0)
    assert res.fob_batch_brl == 20.0
    assert res.unit_landed_cost_brl == res.total_batch_landed_cost_brl

def test_wholesale_resale_invalid_margin_fee():
    with pytest.raises(ValueError, match="strictly less than 1.0"):
        simulate_wholesale_resale(batch_landed_cost_brl=100.0, moq=10, target_margin_pct=0.60, marketplace_fee_pct=0.40)

def test_wholesale_resale_zero_landed_cost():
    resale = simulate_wholesale_resale(batch_landed_cost_brl=0.0, moq=10, target_margin_pct=0.30, marketplace_fee_pct=0.15)
    assert resale.roi_pct == 0.0
    assert resale.unit_sale_price_brl == 0.0
    assert resale.projected_net_profit_brl == 0.0
