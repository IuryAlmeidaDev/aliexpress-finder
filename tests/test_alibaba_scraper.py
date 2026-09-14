from unittest.mock import MagicMock, patch
from src.clients.alibaba_scraper import (
    parse_moq,
    parse_alibaba_price,
    parse_alibaba_html_items,
    DirectAlibabaClient,
)

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

    # Thousands formatting tests
    assert parse_alibaba_price("$1,200.00", usd_rate=5.50) == round(1200.00 * 5.50, 2)
    assert parse_alibaba_price("R$ 1.250,90", usd_rate=5.50) == 1250.90
    assert parse_alibaba_price("$1,500", usd_rate=5.50) == round(1500.00 * 5.50, 2)

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

def test_direct_alibaba_client_search():
    client = DirectAlibabaClient(usd_rate=5.50)
    assert client.timeout == 15
    assert client.usd_rate == 5.50

    html_with_duplicate = MOCK_ALIBABA_HTML + """
    <div class="organic-list-offer-outter" data-spm="offer">
        <a class="organic-gallery-title" href="//www.alibaba.com/product-detail/Custom-Kids-Digital-Watch_1600123456.html">
            Custom Kids Digital Watch Duplicate
        </a>
        <div class="element-offer-price">$0.85</div>
        <div class="element-offer-minorder">Min. order: 50 pieces</div>
    </div>
    """

    mock_resp = MagicMock()
    mock_resp.text = html_with_duplicate
    mock_resp.raise_for_status.return_value = None

    with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
        results = client.search("watch", max_items=2)
        assert len(results) == 2
        assert results[0]["id"] == "1600123456"
        assert results[1]["id"] == "1600999999"
        # Deduplication check: duplicate item 1600123456 was ignored
        assert len({it["id"] for it in results}) == 2
        mock_get.assert_called_once()

        # Limiting check: max_items=1 limits results to 1 item
        single_result = client.search("watch", max_items=1)
        assert len(single_result) == 1
        assert single_result[0]["id"] == "1600123456"
