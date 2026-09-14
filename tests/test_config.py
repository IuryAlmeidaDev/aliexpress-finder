import os
from src.config import Config, load_config

def test_default_config():
    cfg = Config()
    assert cfg.DEFAULT_USD_BRL > 0
    assert cfg.DEFAULT_ICMS_RATE == 0.17
    assert cfg.DEFAULT_MARKETPLACE_FEE == 0.16
    assert cfg.DEFAULT_TARGET_MARGIN == 0.40
    assert cfg.MIN_STORE_RATING == 4.5
    assert cfg.MIN_SALES_COUNT == 10

def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_USD_BRL", "6.00")
    monkeypatch.setenv("DEFAULT_ICMS_RATE", "0.20")
    cfg = load_config()
    assert cfg.DEFAULT_USD_BRL == 6.00
    assert cfg.DEFAULT_ICMS_RATE == 0.20
