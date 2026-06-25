"""The shared tool response envelope, response-size policy, and error taxonomy.

Every VaultPilot tool returns ``{ "data", "meta", "warnings" }`` (harvested from
the TS design branch). List-heavy tools honor a response-size policy: a default
``detail="summary"`` view, an optional ``detail="full"`` expansion, and a hard
``limit`` cap with truncation noted in ``meta``/``warnings``.
"""

from __future__ import annotations

from typing import Any, Literal

Detail = Literal["summary", "full"]

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


def envelope(
    request_id: str,
    detail: Detail,
    data: Any,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Wrap a tool payload in the standard envelope."""
    return {
        "data": data,
        "meta": {"requestId": request_id, "detail": detail},
        "warnings": list(warnings or []),
    }


def normalize_limit(limit: int | None) -> tuple[int, list[str]]:
    """Clamp a requested limit into ``[1, MAX_LIMIT]``.

    Returns the effective limit plus any warnings describing clamping, so callers
    can fold them into the envelope rather than silently truncating.
    """
    warnings: list[str] = []
    if limit is None:
        return DEFAULT_LIMIT, warnings
    if limit < 1:
        warnings.append(f"limit {limit} below minimum; using 1.")
        return 1, warnings
    if limit > MAX_LIMIT:
        warnings.append(f"limit {limit} exceeds max {MAX_LIMIT}; using {MAX_LIMIT}.")
        return MAX_LIMIT, warnings
    return limit, warnings


# --- Error taxonomy -------------------------------------------------------
# Bungie failures (and our own input failures) normalize into these so tools
# fail predictably. Raw tokens must never appear in messages.


class VaultPilotError(Exception):
    """Base class for all VaultPilot errors."""

    code = "error"


class InvalidInputError(VaultPilotError):
    code = "invalid_input"


class AuthError(VaultPilotError):
    code = "auth_error"


class RateLimitError(VaultPilotError):
    code = "rate_limit"


class UpstreamError(VaultPilotError):
    code = "upstream_error"


class NotFoundError(VaultPilotError):
    code = "not_found"
