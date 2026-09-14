from src.clients.direct_scraper import parse_aliexpress_html_items, parse_price, parse_sales

MOCK_HTML = """
<div class="search-item-card" data-product-id="1005001234">
    <a class="item-link" href="//www.aliexpress.com/item/1005001234.html"></a>
    <h1 class="multi--titleText--nXeOvyr">Pagani Design 40mm Sapphire NH35 Automatic Watch</h1>
    <div class="multi--price-sale--2D-y04C">R$ 190,50</div>
    <span class="multi--trade--Ktbl2jB">150 vendidos</span>
    <span class="multi--evaluation--1a2b3c">4.8</span>
</div>
"""

def test_parse_price_formats():
    assert parse_price("R$ 190,50") == 190.50
    assert parse_price("R$ 1.250,90") == 1250.90
    assert parse_price("US $35.00") == 35.00
    assert parse_price("") == 0.0

def test_parse_sales_formats():
    assert parse_sales("150 vendidos") == 150
    assert parse_sales("1.5k+ vendidos") == 1500
    assert parse_sales("Sem vendas") == 0

def test_parse_aliexpress_items():
    items = parse_aliexpress_html_items(MOCK_HTML)
    assert len(items) == 1
    assert items[0]["id"] == "1005001234"
    assert "Pagani Design" in items[0]["title"]
    assert items[0]["price"] == 190.50
    assert items[0]["sales"] == 150
    assert items[0]["rating"] == 4.8
    assert "aliexpress.com/item/1005001234.html" in items[0]["url"]
