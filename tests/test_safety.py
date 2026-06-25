"""Safety-guardrail tests (PLAN.md §12).

VaultPilot is read + act but never destructive, and its advisory text must avoid
destructive language. These tests encode those invariants.
"""

import json

from vaultpilot.services.recommendation_engine import BANNED_TERMS
from vaultpilot.tools.registry import build_default_context
from vaultpilot.tools import registry as r


def test_recommendations_avoid_destructive_language():
    ctx = build_default_context()
    text = json.dumps(r.recommendations_get(ctx, limit=10)).lower()
    offenders = [term for term in BANNED_TERMS if term in text]
    assert not offenders, f"recommendation text used banned terms: {offenders}"


def test_write_tools_report_non_destructive():
    ctx = build_default_context()
    result = r.transfer_item(ctx, "1001", "character", character_id="2305843009991000001")
    assert any("destroyed" in w.lower() for w in result["warnings"])


def test_no_destructive_tool_exists():
    # The act surface is limited to move/equip — nothing that deletes items.
    public = {name for name in dir(r) if not name.startswith("_")}
    for forbidden in ("dismantle_item", "delete_item", "shard_item", "vendor_sell"):
        assert forbidden not in public
