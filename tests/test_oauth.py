"""M2 OAuth tests — fixtures only, no network, deterministic clock."""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from vaultpilot.auth.callback import parse_callback
from vaultpilot.auth.manager import OAuthManager
from vaultpilot.auth.oauth import OAuthConfig, build_authorize_url, exchange_code, refresh_tokens
from vaultpilot.auth.token_store import FileTokenStore, StoredToken
from vaultpilot.envelope import AuthError

T0 = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def config():
    return OAuthConfig(
        client_id="cid",
        client_secret="csecret",
        api_key="apikey",
        redirect_uri="https://localhost:7777/callback",
    )


def _token_client(expected_grant: str, *, with_refresh: bool = True) -> httpx.Client:
    """An httpx.Client whose transport asserts the request and returns a token."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/App/OAuth/Token/")
        assert request.headers["X-API-Key"] == "apikey"
        assert request.headers["Authorization"].startswith("Basic ")
        body = parse_qs(request.content.decode())
        assert body["grant_type"][0] == expected_grant
        payload = {
            "access_token": "ACCESS-1",
            "token_type": "Bearer",
            "expires_in": 3600,
            "membership_id": "999",
        }
        if with_refresh:
            payload["refresh_token"] = "REFRESH-1"
            payload["refresh_expires_in"] = 7776000
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


# --- authorize URL ---

def test_build_authorize_url_has_no_scope_param(config):
    url = build_authorize_url(config, state="xyz")
    q = parse_qs(urlparse(url).query)
    assert q["client_id"] == ["cid"]
    assert q["response_type"] == ["code"]
    assert q["state"] == ["xyz"]
    assert "scope" not in q  # Bungie ignores scope; we must not send it


# --- token exchange + refresh ---

def test_exchange_code(config):
    resp = exchange_code(config, "the-code", client=_token_client("authorization_code"))
    assert resp.access_token == "ACCESS-1"
    assert resp.refresh_token == "REFRESH-1"
    assert resp.membership_id == "999"


def test_refresh_tokens(config):
    resp = refresh_tokens(config, "REFRESH-1", client=_token_client("refresh_token"))
    assert resp.access_token == "ACCESS-1"


# --- token store round-trip ---

def test_token_store_roundtrip_and_perms(tmp_path, config):
    store = FileTokenStore(tmp_path / "tok.json")
    assert store.load() is None
    resp = exchange_code(config, "c", client=_token_client("authorization_code"))
    token = StoredToken.from_response(resp, T0)
    store.save(token)

    loaded = store.load()
    assert loaded is not None
    assert loaded.access_token == "ACCESS-1"
    assert loaded.access_expires_at == T0 + timedelta(seconds=3600)
    # owner-only perms on POSIX
    import os
    import stat
    mode = stat.S_IMODE(os.stat(tmp_path / "tok.json").st_mode)
    assert mode == 0o600

    store.clear()
    assert store.load() is None


# --- expiry / refresh logic via the manager (injected clock) ---

def _manager(config, tmp_path, *, now, grant, with_refresh=True):
    store = FileTokenStore(tmp_path / "tok.json")
    return OAuthManager(config, store, now=lambda: now,
                        client=_token_client(grant, with_refresh=with_refresh)), store


def test_valid_token_returns_fresh_without_refresh(config, tmp_path):
    mgr, store = _manager(config, tmp_path, now=T0, grant="authorization_code")
    mgr.complete_authorization("code")  # saves ACCESS-1 valid for 1h
    # Same instant: token is fresh, no refresh needed.
    assert mgr.valid_access_token() == "ACCESS-1"


def test_expired_access_triggers_refresh(config, tmp_path):
    store = FileTokenStore(tmp_path / "tok.json")
    # Seed an already-expired access token with a still-valid refresh token.
    store.save(StoredToken(
        access_token="OLD",
        refresh_token="REFRESH-1",
        access_expires_at=T0,
        refresh_expires_at=T0 + timedelta(days=90),
    ))
    later = T0 + timedelta(hours=2)
    mgr = OAuthManager(config, store, now=lambda: later,
                       client=_token_client("refresh_token"))
    assert mgr.valid_access_token() == "ACCESS-1"  # refreshed
    assert store.load().access_token == "ACCESS-1"  # persisted


def test_missing_token_raises(config, tmp_path):
    mgr = OAuthManager(config, FileTokenStore(tmp_path / "none.json"), now=lambda: T0)
    with pytest.raises(AuthError):
        mgr.valid_access_token()


def test_dead_refresh_token_requires_reauth(config, tmp_path):
    store = FileTokenStore(tmp_path / "tok.json")
    store.save(StoredToken(
        access_token="OLD",
        refresh_token="REFRESH-1",
        access_expires_at=T0,
        refresh_expires_at=T0 + timedelta(days=1),
    ))
    way_later = T0 + timedelta(days=400)
    mgr = OAuthManager(config, store, now=lambda: way_later)
    with pytest.raises(AuthError):
        mgr.valid_access_token()


# --- callback parsing ---

def test_parse_callback_extracts_code():
    code = parse_callback("/callback?code=abc123&state=S", expected_state="S")
    assert code == "abc123"


def test_parse_callback_full_url():
    code = parse_callback("https://localhost:7777/callback?code=z&state=S", expected_state="S")
    assert code == "z"


def test_parse_callback_state_mismatch():
    with pytest.raises(AuthError):
        parse_callback("/callback?code=abc&state=WRONG", expected_state="S")


def test_parse_callback_bungie_error():
    with pytest.raises(AuthError):
        parse_callback("/callback?error=access_denied&state=S", expected_state="S")
