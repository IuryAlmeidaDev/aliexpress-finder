import json
import urllib.parse

from src.mercado_livre.oauth_setup import (
    authorization_url,
    parse_callback,
    pkce_pair,
    save_credentials,
)


def test_pkce_authorization_url_and_state_validation():
    verifier, challenge = pkce_pair()
    assert 43 <= len(verifier) <= 128
    url = authorization_url("123", "https://localhost.com/redirect", "state1", challenge)
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert params["client_id"] == ["123"]
    assert params["code_challenge_method"] == ["S256"]
    callback = "https://localhost.com/redirect?code=TG-code&state=state1"
    assert parse_callback(callback, "state1") == "TG-code"


def test_rejects_callback_with_wrong_state():
    try:
        parse_callback("https://localhost.com/redirect?code=x&state=wrong", "right")
    except ValueError as exc:
        assert "state" in str(exc)
    else:
        assert False


def test_saves_credentials_without_printing_or_env_file(tmp_path):
    destination = tmp_path / "token.json"
    save_credentials(
        str(destination), "client", "secret",
        {"access_token": "access", "refresh_token": "refresh"},
    )
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload == {
        "client_id": "client", "client_secret": "secret",
        "access_token": "access", "refresh_token": "refresh",
    }
