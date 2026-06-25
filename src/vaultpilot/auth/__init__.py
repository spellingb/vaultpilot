"""Bungie OAuth2 + token storage (M2).

This package implements the authorization-code flow against the Bungie.net API:

- ``oauth``        — authorize-URL builder, code→token exchange, refresh.
- ``token_store``  — durable, owner-only file persistence of tokens.
- ``callback``     — a loopback HTTP(S) handler to capture the redirect ``code``.
- ``manager``      — ties config + store together and guarantees a fresh token.

The HTTP-calling functions accept an injected ``httpx.Client`` so they can be
driven by ``httpx.MockTransport`` in tests without any network access.
"""

from .manager import OAuthManager
from .oauth import OAuthConfig, TokenResponse, build_authorize_url, exchange_code, refresh_tokens
from .token_store import FileTokenStore, StoredToken

__all__ = [
    "OAuthConfig",
    "TokenResponse",
    "build_authorize_url",
    "exchange_code",
    "refresh_tokens",
    "FileTokenStore",
    "StoredToken",
    "OAuthManager",
]
