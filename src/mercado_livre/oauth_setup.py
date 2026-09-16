"""Assistente interativo para a autorização inicial do Mercado Livre."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import requests


AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
DEFAULT_REDIRECT_URI = "https://api.monvix.me/oauth/mercado-livre/callback"


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def authorization_url(client_id: str, redirect_uri: str, state: str, challenge: str) -> str:
    query = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    return f"{AUTH_URL}?{query}"


def parse_callback(value: str, expected_state: str) -> str:
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urllib.parse.urlparse(value)
        params = urllib.parse.parse_qs(parsed.query)
        state = (params.get("state") or [""])[0]
        if state != expected_state:
            raise ValueError("O state do retorno não corresponde à autorização iniciada.")
        code = (params.get("code") or [""])[0]
    else:
        code = value
    if not code:
        raise ValueError("Código de autorização ausente.")
    return code


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    verifier: str,
    session: Any = requests,
) -> dict[str, Any]:
    response = session.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        description = ""
        try:
            description = str(response.json().get("error_description") or response.text)
        except ValueError:
            description = response.text
        raise RuntimeError(f"O Mercado Livre recusou a troca do código: {description}") from exc
    payload = response.json()
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise RuntimeError("A resposta não contém access token e refresh token.")
    return payload


def save_credentials(
    path: str,
    client_id: str,
    client_secret: str,
    payload: dict[str, Any],
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
    }), encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, destination)


def run(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Autoriza o Radar Mercado Livre via OAuth 2.0 + PKCE")
    parser.add_argument("--client-id", default="", help="App ID criado no DevCenter")
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument("--token-file", default="data/mercado_livre_token.json")
    args = parser.parse_args(argv)

    stored: dict[str, Any] = {}
    token_path = Path(args.token_file)
    if token_path.exists():
        try:
            stored = json.loads(token_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            stored = {}

    client_id = args.client_id.strip() or str(stored.get("client_id") or "").strip()
    if not client_id:
        client_id = input("Client ID (App ID): ").strip()
    client_secret = str(stored.get("client_secret") or "").strip()
    if not client_secret:
        client_secret = getpass.getpass("Client Secret: ").strip()
    if not client_id or not client_secret:
        print("Client ID e Client Secret são obrigatórios.", file=sys.stderr)
        return 1

    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(24)
    url = authorization_url(client_id, args.redirect_uri, state, challenge)
    print("\nAbra este endereço no navegador, faça login e autorize a aplicação:\n")
    print(url)
    print("\nO redirecionamento pode exibir erro porque localhost.com não hospeda a aplicação.")
    callback = input("Cole aqui a URL completa exibida na barra do navegador: ")
    try:
        code = parse_callback(callback, state)
        payload = exchange_code(client_id, client_secret, code, args.redirect_uri, verifier)
        save_credentials(args.token_file, client_id, client_secret, payload)
    except (ValueError, RuntimeError) as exc:
        print(f"Falha na autorização: {exc}", file=sys.stderr)
        return 1
    print(f"Autorização concluída. Credenciais salvas com acesso restrito em {args.token_file}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
