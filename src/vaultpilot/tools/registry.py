"""Tool logic, decoupled from the MCP transport.

Each function here is a plain, directly-testable callable that takes a
``ToolContext`` plus validated inputs and returns the standard envelope. The
MCP server (``server.py``) registers thin ``@mcp.tool()`` wrappers around these.
Keeping the logic out of the decorators is what lets the contract tests run
without importing the MCP SDK.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..envelope import Detail, InvalidInputError, envelope, normalize_limit
from ..services import (
    AuthService,
    MockAuthService,
    MockProfileService,
    MockRecommendationEngine,
    ProfileService,
    RecommendationEngine,
)

MOCK_WARNING = "Mock data only; no live Bungie integration yet (M0/M1)."


@dataclass
class ToolContext:
    auth_service: AuthService
    profile_service: ProfileService
    recommendation_engine: RecommendationEngine


def build_default_context() -> ToolContext:
    """The mock-backed context used until real Bungie services land (M2+)."""
    return ToolContext(
        auth_service=MockAuthService(),
        profile_service=MockProfileService(),
        recommendation_engine=MockRecommendationEngine(),
    )


def _items_payload(items, detail: Detail) -> list[dict]:
    if detail == "full":
        return [i.model_dump() for i in items]
    # summary view: drop the noisier fields
    return [
        {"item_instance_id": i.item_instance_id, "name": i.name,
         "bucket": i.bucket, "power": i.power}
        for i in items
    ]


# --- auth & system -------------------------------------------------------

def auth_start(ctx: ToolContext, request_id: str = "req-local") -> dict:
    return envelope(request_id, "summary", ctx.auth_service.start_auth())


def auth_status(ctx: ToolContext, request_id: str = "req-local") -> dict:
    return envelope(request_id, "summary", ctx.auth_service.get_status())


def auth_logout(ctx: ToolContext, request_id: str = "req-local") -> dict:
    return envelope(request_id, "summary", ctx.auth_service.logout())


def manifest_status_get(ctx: ToolContext, request_id: str = "req-local") -> dict:
    data = {"version": "mock-manifest-v1", "updated_at": "2026-06-25T00:00:00Z", "stale": False}
    return envelope(request_id, "summary", data, [MOCK_WARNING])


# --- reads ---------------------------------------------------------------

def get_account_summary(ctx: ToolContext, request_id: str = "req-local",
                        detail: Detail = "summary") -> dict:
    profile = ctx.profile_service.get_profile()
    return envelope(request_id, detail, profile.model_dump(), [MOCK_WARNING])


def get_vault(ctx: ToolContext, request_id: str = "req-local",
              detail: Detail = "summary", limit: int = 25) -> dict:
    eff_limit, warnings = normalize_limit(limit)
    items = ctx.profile_service.get_vault_items(eff_limit)
    data = {"items": _items_payload(items, detail), "cursor": None, "returned": len(items)}
    return envelope(request_id, detail, data, warnings + [MOCK_WARNING])


def get_character_inventory(ctx: ToolContext, character_id: str,
                            request_id: str = "req-local",
                            detail: Detail = "summary", limit: int = 25) -> dict:
    if not character_id:
        raise InvalidInputError("character_id is required.")
    eff_limit, warnings = normalize_limit(limit)
    items = ctx.profile_service.get_character_inventory(character_id, eff_limit)
    data = {"character_id": character_id, "items": _items_payload(items, detail),
            "cursor": None, "returned": len(items)}
    return envelope(request_id, detail, data, warnings + [MOCK_WARNING])


def get_currencies(ctx: ToolContext, request_id: str = "req-local",
                   detail: Detail = "summary") -> dict:
    return envelope(request_id, detail, ctx.profile_service.get_currencies(), [MOCK_WARNING])


def get_quests(ctx: ToolContext, request_id: str = "req-local",
               detail: Detail = "summary", limit: int = 25) -> dict:
    eff_limit, warnings = normalize_limit(limit)
    items = ctx.profile_service.get_quests_bounties(eff_limit)
    data = {"items": items, "cursor": None, "returned": len(items)}
    return envelope(request_id, detail, data, warnings + [MOCK_WARNING])


def recommendations_get(ctx: ToolContext, request_id: str = "req-local",
                        detail: Detail = "summary", limit: int = 25) -> dict:
    eff_limit, warnings = normalize_limit(limit)
    recs = ctx.recommendation_engine.get_recommendations(eff_limit)
    data = [r.model_dump() for r in recs]
    return envelope(request_id, detail, data, warnings + [MOCK_WARNING])


# --- writes (read + act) -------------------------------------------------

def transfer_item(ctx: ToolContext, item_instance_id: str, destination: str,
                  character_id: str | None = None, request_id: str = "req-local") -> dict:
    if destination not in ("vault", "character"):
        raise InvalidInputError("destination must be 'vault' or 'character'.")
    if destination == "character" and not character_id:
        raise InvalidInputError("character_id is required when destination is 'character'.")
    result = ctx.profile_service.transfer_item(item_instance_id, destination, character_id)
    return envelope(request_id, "summary", result,
                    [MOCK_WARNING, "Reversible transfer; no items were destroyed."])


def equip_item(ctx: ToolContext, item_instance_id: str, character_id: str,
               request_id: str = "req-local") -> dict:
    if not character_id:
        raise InvalidInputError("character_id is required.")
    result = ctx.profile_service.equip_item(item_instance_id, character_id)
    return envelope(request_id, "summary", result, [MOCK_WARNING])
