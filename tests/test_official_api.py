from src.clients.official_api import generate_top_signature, OfficialAliExpressClient

def test_generate_top_signature():
    secret = "my_secret_key"
    params = {
        "app_key": "12345678",
        "method": "aliexpress.affiliate.product.query",
        "timestamp": "2026-09-14 00:00:00",
        "format": "json",
        "v": "2.0",
        "sign_method": "sha256",
        "keywords": "watch",
    }
    sign = generate_top_signature(params, secret)
    assert isinstance(sign, str)
    assert len(sign) == 64  # SHA256 hex string length
    assert sign == generate_top_signature(params, secret)

def test_official_client_configuration():
    client_unconfigured = OfficialAliExpressClient("", "")
    assert client_unconfigured.is_configured() is False
    assert client_unconfigured.search("test") == []

    client_configured = OfficialAliExpressClient("my_app_key", "my_app_secret")
    assert client_configured.is_configured() is True
