from src.clients.alibaba_scraper import parse_moq, parse_alibaba_price, parse_alibaba_html_items

MOCK_ALIBABA_HTML = """
<div class="organic-list-offer-outter" data-spm="offer">
    <a class="organic-gallery-title" href="//www.alibaba.com/product-detail/Custom-Kids-Digital-Watch_1600123456.html">
        Custom Kids Digital Watch Colorful Silicone LED Student Watch
    </a>
    <div class="element-offer-price">$0.85 - $1.20</div>
    <div class="element-offer-minorder">Min. order: 50 pieces</div>
    <div class="organic-gallery-offer__seller-company">Shenzhen Top Time Watch Co., Ltd.</div>
    <span class="verified-icon">Verified Supplier</span>
    <span class="trade-assurance-icon">Trade Assurance</span>
    <span class="seller-tag__years">5 yrs</span>
</div>
<div class="organic-list-offer-outter" data-spm="offer">
    <a class="organic-gallery-title" href="//www.alibaba.com/product-detail/Smart-Watch-Teen_1600999999.html">
        Smart Watch Teen Unbranded
    </a>
    <div class="element-offer-price">R$ 15,50</div>
    <div class="element-offer-minorder">100 sets</div>
    <div class="organic-gallery-offer__seller-company">Guangzhou Fashion Trading</div>
</div>
"""

def test_parse_moq():
    assert parse_moq("Min. order: 50 pieces") == 50
    assert parse_moq("100 sets") == 100
    assert parse_moq("1 piece") == 1
    assert parse_moq("MOQ: 500 pcs") == 500
    assert parse_moq("") == 1

def test_parse_alibaba_price():
    # USD conversion (usd_rate=5.50)
    assert parse_alibaba_price("$0.85 - $1.20", usd_rate=5.50) == round(0.85 * 5.50, 2)
    assert parse_alibaba_price("$2.50", usd_rate=5.50) == round(2.50 * 5.50, 2)
    # BRL direct
    assert parse_alibaba_price("R$ 15,50", usd_rate=5.50) == 15.50
    assert parse_alibaba_price("", usd_rate=5.50) == 0.0

def test_parse_alibaba_html_items():
    items = parse_alibaba_html_items(MOCK_ALIBABA_HTML, usd_rate=5.50)
    assert len(items) == 2

    first = items[0]
    assert first["id"] == "1600123456"
    assert "Custom Kids Digital Watch" in first["title"]
    assert first["price"] == round(0.85 * 5.50, 2)
    assert first["moq"] == 50
    assert first["supplier_name"] == "Shenzhen Top Time Watch Co., Ltd."
    assert first["is_verified"] is True
    assert first["has_trade_assurance"] is True
    assert first["years_in_business"] == 5
    assert "alibaba.com/product-detail/Custom-Kids-Digital-Watch_1600123456.html" in first["url"]

    second = items[1]
    assert second["moq"] == 100
    assert second["price"] == 15.50
    assert second["is_verified"] is False
    assert second["has_trade_assurance"] is False
    assert second["years_in_business"] == 0
