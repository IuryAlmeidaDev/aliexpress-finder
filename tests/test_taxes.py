import pytest
from src.finance.taxes import calculate_import_taxes

def test_under_50_usd_tax():
    res = calculate_import_taxes(product_price_brl=100.0, shipping_fee_brl=10.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert res.is_under_50_usd is True
    assert pytest.approx(res.customs_value_brl, 0.01) == 110.0
    assert pytest.approx(res.import_tax_brl, 0.01) == 22.0
    assert pytest.approx(res.icms_tax_brl, 0.01) == 27.04
    assert pytest.approx(res.total_taxes_brl, 0.01) == 49.04
    assert pytest.approx(res.total_landed_cost_brl, 0.01) == 159.04

def test_over_50_usd_tax():
    res = calculate_import_taxes(product_price_brl=500.0, shipping_fee_brl=50.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert res.is_under_50_usd is False
    assert pytest.approx(res.import_tax_brl, 0.01) == 220.0
    assert pytest.approx(res.icms_tax_brl, 0.01) == 157.71
    assert pytest.approx(res.total_taxes_brl, 0.01) == 377.71
    assert pytest.approx(res.total_landed_cost_brl, 0.01) == 927.71

def test_invalid_tax_rates():
    with pytest.raises(ValueError):
        calculate_import_taxes(100.0, usd_brl_rate=-1.0)
    with pytest.raises(ValueError):
        calculate_import_taxes(100.0, icms_rate=1.0)
