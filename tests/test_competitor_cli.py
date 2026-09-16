import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from src.cli.main import run
from src.competitors.models import TargetProduct, CompetitorProduct

@pytest.fixture
def mock_target_product():
    return TargetProduct(
        title="Óculos De Sol Quadrado UV400",
        url="https://produto.mercadolivre.com.br/MLB-123",
        reference_price_brl=60.0,
        clean_query="oculos de sol quadrado uv400",
        kit_items=["estojo"]
    )

@pytest.fixture
def mock_competitors():
    return [
        CompetitorProduct(
            title="Óculos Quadrado Premium + Case",
            url="https://produto.mercadolivre.com.br/MLB-456",
            store_name="Ótica Exemplo",
            platform="Mercado Livre",
            price_brl=55.0,
            shipping_type="Full",
            kit_items=["estojo"],
            differentials=["Entrega Full"]
        )
    ]

def test_cli_concorrencia_url_flow(monkeypatch, mock_target_product, mock_competitors):
    monkeypatch.setattr(sys, "argv", ["main.py", "concorrencia", "--url", "https://produto.mercadolivre.com.br/MLB-123"])

    with patch("src.competitors.extractors.router.fetch_product_from_url", return_value=mock_target_product), \
         patch("src.competitors.radar.CompetitorRadar.find_competitors", return_value=mock_competitors):
        run()

def test_cli_concorrencia_termo_with_export(monkeypatch, mock_competitors, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", "concorrencia", "--termo", "relogio safira", "--exportar"])

    with patch("src.competitors.radar.CompetitorRadar.find_competitors", return_value=mock_competitors):
        run()
        assert os.path.exists("dossie_mercado.md")
        assert os.path.exists("benchmarking_concorrencia.xlsx")
