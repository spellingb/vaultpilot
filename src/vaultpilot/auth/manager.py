"""Ties OAuth config + token store together and guarantees a fresh token.

``OAuthManager.valid_access_token()`` is what the Bungie API client (M4) will
call before every request: it returns a non-expired access token, transparently
refreshing when needed, and raises ``AuthError`` when the user must re-authorize.

The clock (``now``) and the ``httpx.Client`` are both injectable so the refresh
path is fully unit-testable against fixtures.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import httpx

from ..envelope import AuthError
from .oauth import OAuthConfig, build_authorize_url, exchange_code, generate_state, refresh_tokens
from .token_store import FileTokenStore, StoredToken, utc_now


class OAuthManager:
    def __init__(
        self,
        config: OAuthConfig,
        store: FileTokenStore,
        *,
        now: Callable[[], datetime] = utc_now,
        client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._store = store
        self._now = now
        self._client = client  # if set, reused for token calls (tests inject a mock)

    # --- authorization (interactive, runs on the user's machine) ---

    def start_authorization(self) -> tuple[str, str]:
        """Return ``(authorize_url, state)`` for the browser step."""
        state = generate_state()
        return build_authorize_url(self._config, state), state

    def complete_authorization(self, code: str) -> StoredToken:
        """Exchange the captured ``code`` and persist the resulting tokens."""
        resp = exchange_code(self._config, code, client=self._client)
        token = StoredToken.from_response(resp, self._now())
        self._store.save(token)
        return token

    # --- token freshness ---

    def valid_access_token(self) -> str:
        """Return a non-expired access token, refreshing if necessary."""
        token = self._store.load()
        if token is None:
            raise AuthError("Not authenticated. Run the authorize flow first.")

        if not token.access_expired(self._now()):
            return token.access_token

        if token.refresh_token is None or token.refresh_expired(self._now()):
            raise AuthError("Session expired. Re-authorization required.")

        resp = refresh_tokens(self._config, token.refresh_token, client=self._client)
        refreshed = StoredToken.from_response(resp, self._now())
        # Bungie may omit a new refresh token; keep the old one if so.
        if refreshed.refresh_token is None:
            refreshed.refresh_token = token.refresh_token
            refreshed.refresh_expires_at = token.refresh_expires_at
        self._store.save(refreshed)
        return refreshed.access_token

    def logout(self) -> None:
        self._store.clear()
