import os

import pandas as pd

from src.mercado_livre.models import RadarProduct
from src.mercado_livre.repository import RadarRepository
from src.mercado_livre.service import MercadoLivreRadar


class FakeClient:
    def validate_configuration(self):
        return None

    def highlights(self, category_id):
        return [{"id": "MLB1", "type": "ITEM", "position": 1}]

    def resolve_highlight(self, entry, category_id):
        return RadarProduct(
            "MLB1", "ITEM", category_id, "Caderno personalizado",
            url="https://produto/1", rank=1, price=40,
            attributes={"BRAND": "Genérica", "COLOR": "Azul", "MATERIAL": "Papel"},
        )

    def add_reviews(self, product, limit):
        product.review_count = 80
        product.review_average = 4.8
        product.review_texts = ["A embalagem chegou amassada"] * 3
        return product


def test_full_radar_run_exports_four_traceable_sheets(tmp_path):
    with RadarRepository(str(tmp_path / "radar.db")) as repo:
        radar = MercadoLivreRadar(FakeClient(), repo, str(tmp_path / "reports"))
        result = radar.run(category_ids=["MLB10"])
    assert result.status == "success"
    assert result.opportunities == 1
    assert os.path.exists(result.report_path)
    workbook = pd.ExcelFile(result.report_path)
    assert workbook.sheet_names == ["Oportunidades", "Investigar", "Evidências", "Execução"]


class MissingTokenClient:
    def validate_configuration(self):
        raise RuntimeError("token ausente")


def test_failed_configuration_does_not_create_success_report(tmp_path):
    with RadarRepository(str(tmp_path / "radar.db")) as repo:
        radar = MercadoLivreRadar(MissingTokenClient(), repo, str(tmp_path / "reports"))
        result = radar.run(category_ids=["MLB10"])
    assert result.status == "failed"
    assert result.report_path is None
    assert "token ausente" in result.errors[0]
