# VaultPilot

VaultPilot is a read-only TypeScript MCP server for Destiny 2 analysis.

This repository currently implements **Phase 1 and Phase 2 (mock-first)**:

- local MCP stdio server scaffold
- tool schemas and registry
- mocked auth/profile/recommendation services
- domain models and minimal tests

It intentionally does **not** include real Bungie OAuth exchange or live Bungie API calls yet.

## Requirements

- Node.js 20+

## Local Development

1. Install dependencies:
   - `npm install`
2. Start the MCP stdio server (mock mode):
   - `npm run dev`
3. Type-check:
   - `npm run typecheck`
4. Build:
   - `npm run build`
5. Run tests:
   - `npm test`

## Environment Variables

Optional environment variables (with defaults):

- `NODE_ENV` (`development`)
- `LOG_LEVEL` (`info`)
- `MCP_SERVER_NAME` (`vaultpilot`)
- `MCP_SERVER_VERSION` (`0.1.0`)
- `OAUTH_CALLBACK_HOST` (`127.0.0.1`)
- `OAUTH_CALLBACK_PORT` (`8787`)

## Implemented Read-Only Tools (Mocked)

- `auth_start`
- `auth_status`
- `auth_logout`
- `manifest_status_get`
- `player_profile_get`
- `vault_items_get`
- `character_inventory_get`
- `currencies_get`
- `quests_bounties_get`
- `recommendations_get`
