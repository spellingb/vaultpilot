"""Durable token persistence.

The MVP store is a local JSON file locked to owner read/write (``0o600``) where
the OS supports it. Absolute expiry instants are stored (not relative
``expires_in``) so freshness can be judged after a restart. A ``StoredToken`` is
built from a ``TokenResponse`` plus the "now" at which it was issued, so the
clock is injectable for deterministic tests.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import BaseModel

from .oauth import TokenResponse


class StoredToken(BaseModel):
    access_token: str
    refresh_token: str | None = None
    access_expires_at: datetime
    refresh_expires_at: datetime | None = None
    membership_id: str | None = None

    @classmethod
    def from_response(cls, resp: TokenResponse, now: datetime) -> "StoredToken":
        refresh_expires_at = (
            now + timedelta(seconds=resp.refresh_expires_in)
            if resp.refresh_expires_in is not None
            else None
        )
        return cls(
            access_token=resp.access_token,
            refresh_token=resp.refresh_token,
            access_expires_at=now + timedelta(seconds=resp.expires_in),
            refresh_expires_at=refresh_expires_at,
            membership_id=resp.membership_id,
        )

    def access_expired(self, now: datetime, *, leeway_seconds: int = 60) -> bool:
        """True if the access token is expired (or within ``leeway`` of it)."""
        return now >= self.access_expires_at - timedelta(seconds=leeway_seconds)

    def refresh_expired(self, now: datetime) -> bool:
        """True if the refresh token can no longer be used (re-auth required)."""
        if self.refresh_expires_at is None:
            return False
        return now >= self.refresh_expires_at


class FileTokenStore:
    def __init__(self, path: str | os.PathLike) -> None:
        self._path = Path(path)

    def load(self) -> StoredToken | None:
        if not self._path.exists():
            return None
        return StoredToken.model_validate_json(self._path.read_text())

    def save(self, token: StoredToken) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Write then tighten perms to owner-only (best-effort; no-op on some OSes).
        self._path.write_text(token.model_dump_json(indent=2))
        try:
            os.chmod(self._path, 0o600)
        except (OSError, NotImplementedError):  # pragma: no cover - platform dependent
            pass

    def clear(self) -> None:
        self._path.unlink(missing_ok=True)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
