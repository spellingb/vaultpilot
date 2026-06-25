"""FastMCP server entrypoint.

Registers every tool from ``tools.registry`` as a thin ``@mcp.tool()`` wrapper
bound to a shared (mock) context, then runs over stdio. Errors in the taxonomy
are caught and returned inside the envelope's ``warnings`` so a misbehaving call
never crashes the transport.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from .config import load_settings
from .envelope import Detail, VaultPilotError
from .tools import build_default_context
from .tools import registry as r

settings = load_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("vaultpilot")

mcp = FastMCP(settings.mcp_server_name)
ctx = build_default_context()


def _guard(fn, *args, **kwargs) -> dict:
    """Run a registry function, mapping taxonomy errors into an error envelope."""
    try:
        return fn(*args, **kwargs)
    except VaultPilotError as exc:
        return {"data": None, "meta": {"requestId": kwargs.get("request_id", "req-local")},
                "warnings": [f"{exc.code}: {exc}"]}


@mcp.tool()
def ping() -> dict:
    """Liveness check — confirms an MCP client can reach the server."""
    return {"data": {"ok": True, "server": settings.mcp_server_name}, "meta": {}, "warnings": []}


# --- auth & system ---

@mcp.tool()
def auth_start(request_id: str = "req-local") -> dict:
    """Start the Bungie OAuth flow; returns an authorize URL + state nonce."""
    return _guard(r.auth_start, ctx, request_id=request_id)


@mcp.tool()
def auth_status(request_id: str = "req-local") -> dict:
    """Return the current auth state (authenticated / missing token)."""
    return _guard(r.auth_status, ctx, request_id=request_id)


@mcp.tool()
def auth_logout(request_id: str = "req-local") -> dict:
    """Clear local auth/token state."""
    return _guard(r.auth_logout, ctx, request_id=request_id)


@mcp.tool()
def manifest_status_get(request_id: str = "req-local") -> dict:
    """Return Destiny manifest cache version / staleness."""
    return _guard(r.manifest_status_get, ctx, request_id=request_id)


# --- reads ---

@mcp.tool()
def get_account_summary(request_id: str = "req-local", detail: Detail = "summary") -> dict:
    """Characters, light/power, and platform — orientation for an account."""
    return _guard(r.get_account_summary, ctx, request_id=request_id, detail=detail)


@mcp.tool()
def get_vault(request_id: str = "req-local", detail: Detail = "summary", limit: int = 25) -> dict:
    """Account vault contents, grouped by item type."""
    return _guard(r.get_vault, ctx, request_id=request_id, detail=detail, limit=limit)


@mcp.tool()
def get_character_inventory(character_id: str, request_id: str = "req-local",
                            detail: Detail = "summary", limit: int = 25) -> dict:
    """Inventory + equipped gear for one character."""
    return _guard(r.get_character_inventory, ctx, character_id,
                  request_id=request_id, detail=detail, limit=limit)


@mcp.tool()
def get_currencies(request_id: str = "req-local", detail: Detail = "summary") -> dict:
    """Glimmer, Legendary Shards, and other currency balances."""
    return _guard(r.get_currencies, ctx, request_id=request_id, detail=detail)


@mcp.tool()
def get_quests(request_id: str = "req-local", detail: Detail = "summary", limit: int = 25) -> dict:
    """Active quests / bounties with status."""
    return _guard(r.get_quests, ctx, request_id=request_id, detail=detail, limit=limit)


@mcp.tool()
def recommendations_get(request_id: str = "req-local", detail: Detail = "summary",
                        limit: int = 25) -> dict:
    """Conservative, advisory, confidence-gated suggestions (never destructive)."""
    return _guard(r.recommendations_get, ctx, request_id=request_id, detail=detail, limit=limit)


# --- writes (read + act) ---

@mcp.tool()
def transfer_item(item_instance_id: str, destination: str, character_id: str | None = None,
                  request_id: str = "req-local") -> dict:
    """Move an item to the vault or to a character. Reversible; never destructive."""
    return _guard(r.transfer_item, ctx, item_instance_id, destination,
                  character_id=character_id, request_id=request_id)


@mcp.tool()
def equip_item(item_instance_id: str, character_id: str, request_id: str = "req-local") -> dict:
    """Equip an item on a character."""
    return _guard(r.equip_item, ctx, item_instance_id, character_id, request_id=request_id)


def main() -> None:
    """Console-script entrypoint: run the MCP server over stdio."""
    logger.info("Starting VaultPilot MCP server (mock mode) over stdio")
    mcp.run()


if __name__ == "__main__":
    main()
