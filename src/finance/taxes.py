from dataclasses import dataclass

@dataclass
class TaxCalculationResult:
    customs_value_brl: float
    customs_value_usd: float
    is_under_50_usd: bool
    import_tax_brl: float
    icms_base_brl: float
    icms_tax_brl: float
    total_taxes_brl: float
    total_landed_cost_brl: float
    is_choice_subsidized: bool = False

def calculate_import_taxes(
    product_price_brl: float,
    shipping_fee_brl: float = 0.0,
    usd_brl_rate: float = 5.50,
    icms_rate: float = 0.17,
    choice_subsidized: bool = False
) -> TaxCalculationResult:
    """
    Calculates Brazilian import taxes according to Remessa Conforme rules:
    - Under or equal to US$ 50: 20% Import Tax (II)
    - Over US$ 50: 60% Import Tax (II) with a fixed deduction of US$ 20
    - Choice subsidy: When AliExpress Choice subsidizes II, Import Tax is R$ 0.00
    - ICMS: Calculated 'por dentro' (grossed-up base): (Customs Value + II) / (1 - ICMS) * ICMS
    """
    if usd_brl_rate <= 0:
        raise ValueError("usd_brl_rate must be greater than 0")
    if icms_rate >= 1.0 or icms_rate < 0:
        raise ValueError("icms_rate must be between 0 and 1 (exclusive of 1)")

    customs_value_brl = round(product_price_brl + shipping_fee_brl, 2)
    customs_value_usd = round(customs_value_brl / usd_brl_rate, 2)
    is_under_50_usd = customs_value_usd <= 50.00

    if choice_subsidized:
        import_tax_brl = 0.0
    elif is_under_50_usd:
        import_tax_brl = round(0.20 * customs_value_brl, 2)
    else:
        gross_ii = 0.60 * customs_value_brl
        deduction = 20.00 * usd_brl_rate
        import_tax_brl = round(max(0.0, gross_ii - deduction), 2)

    icms_base = (customs_value_brl + import_tax_brl) / (1.0 - icms_rate)
    icms_tax_brl = round(icms_base * icms_rate, 2)
    icms_base_brl = round(icms_base, 2)

    total_taxes_brl = round(import_tax_brl + icms_tax_brl, 2)
    total_landed_cost_brl = round(customs_value_brl + total_taxes_brl, 2)

    return TaxCalculationResult(
        customs_value_brl=customs_value_brl,
        customs_value_usd=customs_value_usd,
        is_under_50_usd=is_under_50_usd,
        import_tax_brl=import_tax_brl,
        icms_base_brl=icms_base_brl,
        icms_tax_brl=icms_tax_brl,
        total_taxes_brl=total_taxes_brl,
        total_landed_cost_brl=total_landed_cost_brl,
        is_choice_subsidized=choice_subsidized,
    )
