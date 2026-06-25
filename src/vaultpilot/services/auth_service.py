"""Auth service protocol + a mock implementation.

The real implementation (M2) will drive the Bungie OAuth2 authorization-code
flow through a localhost callback and persist tokens. The mock just toggles an
in-memory authenticated flag so the auth tools have predictable behavior.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class AuthStartResult(TypedDict):
    authorize_url: str
    state: str
    callback_url: str


class AuthStatus(TypedDict, total=False):
    state: str  # "authenticated" | "missing_token"
    account_display_name: str


class AuthService(Protocol):
    def start_auth(self) -> AuthStartResult: ...
    def get_status(self) -> AuthStatus: ...
    def logout(self) -> AuthStatus: ...


class MockAuthService:
    """In-memory mock. No real OAuth, no network, no tokens."""

    def __init__(self) -> None:
        self._authenticated = False

    def start_auth(self) -> AuthStartResult:
        # Real flow will generate a CSRF state nonce and a real authorize URL.
        self._authenticated = True
        return {
            "authorize_url": "https://www.bungie.net/en/OAuth/Authorize?client_id=mock&response_type=code",
            "state": "mock-state-123",
            "callback_url": "https://localhost:7777/callback",
        }

    def get_status(self) -> AuthStatus:
        if not self._authenticated:
            return {"state": "missing_token"}
        return {"state": "authenticated", "account_display_name": "MockGuardian#1234"}

    def logout(self) -> AuthStatus:
        self._authenticated = False
        return {"state": "missing_token"}
