import pytest
from src.finance.margins import simulate_resale

def test_simulate_resale_margin():
    # Landed Cost = R$ 100. Marketplace Fee = 16%. Target Net Margin = 40% on sale price.
    # Formula: Sale Price = Landed Cost / (1 - marketplace_fee_pct - target_margin_pct)
    # S = 100 / (1 - 0.16 - 0.40) = 100 / 0.44 = 227.27
    # Fee = 227.27 * 0.16 = 36.36
    # Net Revenue = 227.27 - 36.36 = 190.91
    # Net Profit = 190.91 - 100 = 90.91 (= 40% of 227.27)
    # ROI = 90.91 / 100 = 90.91%
    res = simulate_resale(landed_cost_brl=100.0, target_margin_pct=0.40, marketplace_fee_pct=0.16)
    assert res.suggested_sale_price_brl == pytest.approx(227.27, abs=0.01)
    assert res.marketplace_fee_brl == pytest.approx(36.36, abs=0.01)
    assert res.net_profit_brl == pytest.approx(90.91, abs=0.01)
    assert res.net_margin_pct == pytest.approx(0.40, abs=0.01)
    assert res.roi_pct == pytest.approx(90.91, abs=0.01)

def test_invalid_margins():
    with pytest.raises(ValueError):
        simulate_resale(100.0, target_margin_pct=0.85, marketplace_fee_pct=0.20)
    with pytest.raises(ValueError):
        simulate_resale(-50.0)
