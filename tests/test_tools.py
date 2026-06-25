"""Contract tests for the mock-first tool surface.

These import the registry functions directly (not the MCP server), so they run
without the MCP SDK installed.
"""

import pytest

from vaultpilot.envelope import MAX_LIMIT, InvalidInputError
from vaultpilot.tools.registry import build_default_context
from vaultpilot.tools import registry as r


@pytest.fixture
def ctx():
    return build_default_context()


def assert_envelope(result):
    assert set(result) == {"data", "meta", "warnings"}
    assert "requestId" in result["meta"]
    assert isinstance(result["warnings"], list)


# --- auth ---

def test_auth_start_then_status_is_authenticated(ctx):
    r.auth_start(ctx)
    status = r.auth_status(ctx)
    assert_envelope(status)
    assert status["data"]["state"] == "authenticated"


def test_auth_logout_clears_state(ctx):
    r.auth_start(ctx)
    r.auth_logout(ctx)
    assert r.auth_status(ctx)["data"]["state"] == "missing_token"


# --- reads ---

def test_account_summary(ctx):
    result = r.get_account_summary(ctx)
    assert_envelope(result)
    assert result["data"]["account"]["display_name"] == "MockGuardian"


def test_vault_summary_vs_full_detail(ctx):
    summary = r.get_vault(ctx, detail="summary")
    full = r.get_vault(ctx, detail="full")
    assert summary["data"]["items"], "expected at least one vault item"
    # full carries fields the summary view omits
    assert "item_hash" not in summary["data"]["items"][0]
    assert "item_hash" in full["data"]["items"][0]


def test_limit_is_clamped_with_warning(ctx):
    result = r.get_vault(ctx, limit=9999)
    assert any(str(MAX_LIMIT) in w for w in result["warnings"])


def test_character_inventory_requires_id(ctx):
    with pytest.raises(InvalidInputError):
        r.get_character_inventory(ctx, character_id="")


# --- writes (read + act) ---

def test_transfer_item_to_vault_echoes_before_after(ctx):
    result = r.transfer_item(ctx, "1002", "vault")
    assert_envelope(result)
    assert result["data"]["after"]["location"] == "vault"
    assert result["data"]["before"]["location"] == "character"


def test_transfer_to_character_requires_character_id(ctx):
    with pytest.raises(InvalidInputError):
        r.transfer_item(ctx, "1001", "character")


def test_transfer_rejects_bad_destination(ctx):
    with pytest.raises(InvalidInputError):
        r.transfer_item(ctx, "1001", "nowhere")


def test_equip_item(ctx):
    result = r.equip_item(ctx, "1003", "2305843009991000002")
    assert result["data"]["after"]["equipped"] is True
