# VaultPilot

VaultPilot is a **read + act** MCP server that lets AI assistants analyze a player's
Destiny 2 inventory, vault, quests, currencies, triumphs, and weekly priorities — and
perform guarded, non-destructive item transfers/equips — using the official
[Bungie.net API](https://bungie-net.github.io/).

See [PLAN.md](PLAN.md) for the full design and milestones.

## Status

**M0 + M1 complete (mock-first).** The full MCP tool surface is wired against mocked
services and runs over stdio. Real Bungie OAuth2 + live data integration is M2+.

## Quick start (development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# run the test suite
pytest

# run the MCP server over stdio (mock mode — no credentials needed)
python -m vaultpilot.server
```

To use real Bungie data later (M2+), copy `.env.example` to `.env` and fill in your
credentials from a [registered Bungie app](https://www.bungie.net/developer). The app
must have **both** the "Read your Destiny 2 information" and "Move or equip Destiny
gear" scopes enabled.

## Tools (mock-first)

- **Auth/system:** `auth_start`, `auth_status`, `auth_logout`, `manifest_status_get`, `ping`
- **Read:** `get_account_summary`, `get_vault`, `get_character_inventory`,
  `get_currencies`, `get_quests`, `recommendations_get`
- **Act (guarded, never destructive):** `transfer_item`, `equip_item`

Every tool returns a `{ data, meta, warnings }` envelope. List tools support
`detail=summary|full` and a capped `limit`. See PLAN.md §12 for safety guarantees.
