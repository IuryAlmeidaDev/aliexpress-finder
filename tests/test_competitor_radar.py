import pytest
from unittest.mock import patch, MagicMock
from src.competitors.radar import CompetitorRadar
from src.competitors.models import CompetitorProduct

MOCK_ML_SEARCH_HTML = """
<!DOCTYPE html>
<html>
<body>
    <ol class="ui-search-layout ui-search-layout--stack">
        <li class="ui-search-layout__item">
            <div class="ui-search-result__content-wrapper">
                <a href="https://produto.mercadolivre.com.br/MLB-1001-oculos-quadrado" class="ui-search-link">
                    <h2 class="ui-search-item__title">Óculos De Sol Quadrado Masculino Acetato Preto UV400 + Estojo</h2>
                </a>
                <div class="ui-search-price__second-line">
                    <span class="andes-money-amount ui-search-price__part">
                        <span class="andes-money-amount__fraction">48</span>
                        <span class="andes-money-amount__cents">90</span>
                    </span>
                </div>
                <span class="ui-search-item__seller-info">Loja Alpha Ótica</span>
                <span class="ui-search-item__fulfillment">FULL</span>
                <span class="ui-search-reviews__rating-number">4.8</span>
                <span class="ui-search-reviews__amount">(1.540)</span>
            </div>
        </li>
        <li class="ui-search-layout__item">
            <div class="ui-search-result__content-wrapper">
                <a href="https://produto.mercadolivre.com.br/MLB-1002-oculos-retro" class="ui-search-link">
                    <h2 class="ui-search-item__title">Óculos Retrô Vintage Unissex Flanela Inclusa</h2>
                </a>
                <div class="ui-search-price__second-line">
                    <span class="andes-money-amount ui-search-price__part">
                        <span class="andes-money-amount__fraction">65</span>
                    </span>
                </div>
                <span class="ui-search-item__seller-info">Beta Store</span>
                <span class="ui-search-item__shipping--free">Frete grátis</span>
                <span class="ui-search-reviews__rating-number">4.6</span>
                <span class="ui-search-reviews__amount">(320)</span>
            </div>
        </li>
    </ol>
</body>
</html>
"""

def test_competitor_radar_parse_html():
    radar = CompetitorRadar()
    competitors = radar.parse_search_html(MOCK_ML_SEARCH_HTML, limit=5)

    assert len(competitors) == 2
    
    c1 = competitors[0]
    assert c1.title == "Óculos De Sol Quadrado Masculino Acetato Preto UV400 + Estojo"
    assert c1.price_brl == 48.90
    assert c1.shipping_type == "Full"
    assert c1.rating == 4.8
    assert "estojo" in c1.kit_items
    assert c1.store_name == "Loja Alpha Ótica"

    c2 = competitors[1]
    assert c2.price_brl == 65.00
    assert c2.shipping_type == "Frete Grátis"
    assert "flanela" in c2.kit_items
    assert c2.store_name == "Beta Store"

@patch("requests.get")
def test_competitor_radar_find_competitors(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = MOCK_ML_SEARCH_HTML
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    radar = CompetitorRadar()
    competitors = radar.find_competitors("oculos quadrado uv400", limit=2)

    assert len(competitors) == 2
    mock_get.assert_called_once()
    assert "oculos-quadrado-uv400" in mock_get.call_args[0][0] or "q=" in mock_get.call_args[0][0]
