import json
import os
import time
from unittest.mock import MagicMock, patch
import pytest

from src.finance.currency import CurrencyRate, get_usd_brl_rate


def test_manual_rate_override():
    """Manual rate should take precedence over everything without network requests."""
    res = get_usd_brl_rate(manual_rate=6.20)
    assert res.rate == 6.20
    assert res.source == "manual"


def test_fetch_from_api_and_cache(tmp_path):
    """Should fetch from API when cache is empty and persist to cache file."""
    cache_file = str(tmp_path / "cache.json")
    mock_payload = json.dumps({
        "USDBRL": {
            "bid": "5.1845",
            "ask": "5.1855",
            "create_date": "2026-09-16 10:00:00"
        }
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = get_usd_brl_rate(cache_file=cache_file, cache_ttl_seconds=3600)
        assert res.rate == 5.1845
        assert res.source == "api"

    # Verify cache file was written
    assert os.path.exists(cache_file)
    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["rate"] == 5.1845


def test_use_valid_cache(tmp_path):
    """Should use local cache if it is within TTL without calling API."""
    cache_file = str(tmp_path / "cache.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({"rate": 5.25, "timestamp": time.time(), "updated_at": "2026-09-16 10:00:00"}, f)

    with patch("urllib.request.urlopen") as mock_url:
        res = get_usd_brl_rate(cache_file=cache_file, cache_ttl_seconds=3600)
        assert res.rate == 5.25
        assert res.source == "cache"
        mock_url.assert_not_called()


def test_fallback_to_stale_cache_when_api_fails(tmp_path):
    """When API fails and cache is expired, return stale cache instead of hard fallback."""
    cache_file = str(tmp_path / "cache.json")
    # Expired cache (2 hours ago, with 1 hour TTL)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({"rate": 5.30, "timestamp": time.time() - 7200, "updated_at": "2026-09-16 08:00:00"}, f)

    with patch("urllib.request.urlopen", side_effect=Exception("Connection error")):
        res = get_usd_brl_rate(cache_file=cache_file, cache_ttl_seconds=3600)
        assert res.rate == 5.30
        assert res.source == "stale_cache"


def test_fallback_to_default_when_no_cache_and_api_fails(tmp_path):
    """When API fails and no cache exists, fallback to provided default_rate."""
    cache_file = str(tmp_path / "non_existent_cache.json")

    with patch("urllib.request.urlopen", side_effect=Exception("Timeout")):
        res = get_usd_brl_rate(cache_file=cache_file, fallback_rate=5.50)
        assert res.rate == 5.50
        assert res.source == "fallback"
