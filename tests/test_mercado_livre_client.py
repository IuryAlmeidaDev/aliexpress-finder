from src.mercado_livre.client import MercadoLivreAuthError, MercadoLivreClient


class FakeResponse:
    def __init__(self, status_code, payload, headers=None):
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_token_is_required():
    client = MercadoLivreClient("")
    try:
        client.root_categories()
    except MercadoLivreAuthError as exc:
        assert "Credenciais do Mercado Livre" in str(exc)
    else:
        assert False


def test_resolves_item_and_reviews_preserving_identity():
    session = FakeSession([
        FakeResponse(200, {
            "id": "MLB1", "title": "Caderno sem marca", "category_id": "MLB10",
            "permalink": "https://produto/1", "price": 39.9,
            "catalog_product_id": "MLB-CAT1",
            "attributes": [{"id": "BRAND", "value_name": "Genérica"}],
        }),
        FakeResponse(200, {
            "paging": {"total": 30}, "rating_average": 4.7,
            "reviews": [{"content": "A embalagem chegou amassada"}],
        }),
    ])
    client = MercadoLivreClient("token", session=session)
    product = client.resolve_highlight({"id": "MLB1", "type": "ITEM", "position": 2}, "MLB10")
    client.add_reviews(product)
    assert product.entity_key == "ITEM:MLB1"
    assert product.catalog_product_id == "MLB-CAT1"
    assert product.rank == 2
    assert product.review_count == 30
    assert product.attributes["BRAND"] == "Genérica"


def test_honors_retry_after_on_rate_limit():
    waits = []
    session = FakeSession([
        FakeResponse(429, {}, {"Retry-After": "0"}),
        FakeResponse(200, []),
    ])
    client = MercadoLivreClient("token", session=session, sleep=waits.append)
    assert client.root_categories() == []
    assert waits == [0.0]


def test_refreshes_and_persists_rotated_token(tmp_path):
    token_file = tmp_path / "token.json"
    session = FakeSession([
        FakeResponse(200, {"access_token": "new", "refresh_token": "rotated"}),
        FakeResponse(200, []),
    ])
    client = MercadoLivreClient(
        "", session=session, client_id="1", client_secret="secret",
        refresh_token="old", token_file=str(token_file),
    )
    assert client.root_categories() == []
    assert client.access_token == "new"
    assert "rotated" in token_file.read_text(encoding="utf-8")
