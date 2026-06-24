# VaultPilot — Implementation Plan

> A **read-only** MCP server that lets AI assistants analyze a player's Destiny 2
> inventory, vault, quests, currencies, triumphs, and weekly priorities using the
> official [Bungie.net API](https://bungie-net.github.io/).

**Status:** Greenfield. The repo currently contains only `README.md` — there is no
connector code yet. This document is the build plan, not a record of work done.

- **Language / runtime:** Python (3.11+)
- **MCP framework:** [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`FastMCP`)
- **Auth:** Full Bungie OAuth2 (Authorization Code flow) so the server reads the
  signed-in user's *own* private inventory and vault.

---

## 1. Why "not functional" today

There is nothing to debug — the connector simply hasn't been built. Everything
below is net-new. The clean slate is an advantage: we can set the auth and manifest
foundations correctly the first time, which is where most Destiny-API projects go
wrong.

## 2. The three hard problems (where the time actually goes)

### 2.1 Bungie OAuth2 — not just an API key
Reading a player's private inventory/vault requires an OAuth2 **access token** with
the `ReadDestinyInventoryAndVault` scope. An API key alone only unlocks public +
manifest data. Key facts (verified against current Bungie docs):

- **Authorize URL:** `https://www.bungie.net/en/OAuth/Authorize`
- **Token URL:** `https://www.bungie.net/Platform/App/OAuth/Token/`
- Every API request must also send the `X-API-Key` header.
- **`ReadDestinyInventoryAndVault`** is the *only* scope a D2 read app needs — it
  covers `profileCurrencies`, `profileInventory`, `characterInventories`,
  vendor receipts, milestones, and progression.
- **Access token lives ~1 hour**; refresh via the token endpoint.
- **Refresh token lives up to 90 days**, renewed for another 90 on each refresh,
  to a hard 1-year ceiling — after which the user must re-authorize.
- Apps can be **Confidential** (has a client secret → use HTTP Basic auth on the
  token endpoint) or **Public**. We'll register a Confidential app.

**Design implication:** we need durable, secure token storage with transparent
refresh-on-expiry. This is the single biggest piece of the project.

### 2.2 The Destiny Manifest
The API returns items as numeric `itemHash` values, not names. To say *"you have 3
Gjallarhorns in your vault"* we must join those hashes against the **Destiny
Manifest** — a large, versioned set of definition tables (item, stat, class,
record/triumph, milestone, etc.).

- Fetch via `GET /Destiny2/Manifest/`, which returns versioned paths to the JSON
  world-content and the mobile SQLite content.
- The manifest is large and changes on each game patch, so it must be **cached on
  disk and version-checked**, not downloaded per request.
- We only need a subset of definition tables for the read features in scope.

### 2.3 MCP tool-surface design
Raw Bungie `GetProfile` responses are deeply nested and enormous. The value
VaultPilot adds is **shaping** that data into compact, LLM-friendly tool outputs so
an assistant can reason without drowning in JSON. Tool outputs should be
manifest-resolved (names, not hashes) and summarized.

---

## 3. Core data flow

```
AI assistant ──(MCP/stdio)──▶ VaultPilot server
                                  │
                                  ├─ ensure valid OAuth token (refresh if stale)
                                  ├─ resolve membershipType + destinyMembershipId
                                  │     via GetMembershipsForCurrentUser
                                  ├─ GET /Destiny2/{type}/Profile/{id}/?components=...
                                  ├─ join itemHashes ▶ cached Manifest definitions
                                  └─ shape ▶ compact JSON ▶ back to assistant
```

Key Bungie endpoints we'll use:
- `GetMembershipsForCurrentUser` — find the player's platform + membership id.
- `Destiny2.GetProfile` with **components** (the workhorse). Relevant components:
  - `100` Profiles, `200` Characters
  - `102` ProfileInventories (**the vault**)
  - `201` CharacterInventories, `205` CharacterEquipment
  - `103/105` Currencies / platform silver, `104` ProfileProgression
  - `202` CharacterProgressions (weekly milestones / "priorities")
  - `900` Records (**triumphs**), `1100` Metrics
- `Destiny2.GetDestinyManifest` — manifest version + paths.

> Note: component numbers and manifest shapes shift over time — confirm against the
> live [API spec](https://bungie-net.github.io/) at implementation time.

---

## 4. Proposed MCP tools

Read-only, manifest-resolved, summarized. First-cut surface:

| Tool | Purpose |
|------|---------|
| `get_account_summary` | Characters, light/power, playtime, platform — orientation. |
| `get_vault` | Account vault contents (component 102), grouped by item type. |
| `get_character_inventory` | Inventory + equipped gear for a character (201/205). |
| `get_currencies` | Glimmer, Legendary Shards, Bright Dust, etc. (103/105). |
| `get_quests` | Active quests / pursuits with step + objective progress. |
| `get_weekly_priorities` | Pinnacle/powerful milestones still available this week (202). |
| `get_triumphs` | Triumph/record progress; filter by completed/incomplete or search. |
| `search_items` | Find items across vault + characters by name/type/tier. |

Each returns a compact dict (names, counts, progress %), never raw Bungie JSON.

## 5. Project layout

```
vaultpilot/
├── README.md
├── PLAN.md                      ← this file
├── pyproject.toml               ← deps: mcp, httpx, (aiosqlite), pydantic
├── .env.example                 ← BUNGIE_API_KEY, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
├── src/vaultpilot/
│   ├── __init__.py
│   ├── server.py                ← FastMCP instance + tool registration
│   ├── config.py                ← env/settings loading
│   ├── auth/
│   │   ├── oauth.py             ← authorize URL, code→token exchange, refresh
│   │   └── token_store.py       ← secure persistence of tokens
│   ├── bungie/
│   │   ├── client.py            ← httpx client; X-API-Key; auto token refresh
│   │   ├── profile.py           ← GetProfile component calls
│   │   └── manifest.py          ← download/cache/version-check + hash lookups
│   ├── tools/                   ← one module per MCP tool (thin: call + shape)
│   └── shaping.py               ← raw Bungie JSON → compact LLM-friendly dicts
└── tests/
    ├── test_manifest.py
    ├── test_shaping.py          ← against recorded fixtures (no live API)
    └── test_oauth.py            ← token refresh logic
```

## 6. Milestones

### M0 — Project scaffold *(no Bungie calls)*
- `pyproject.toml`, package skeleton, `FastMCP` server that starts over stdio.
- One stub tool (`ping`) to confirm an MCP client can connect.
- **Done when:** server registers and responds in an MCP client.

### M1 — Bungie OAuth2
- Register a Confidential app on Bungie.net; capture key/id/secret/redirect.
- Authorization-code flow: build authorize URL, run a tiny local redirect handler
  to capture `code`, exchange for tokens.
- Token store with automatic refresh-on-expiry; handle the 90-day/1-year limits.
- **Done when:** server holds a valid access token and refreshes transparently.

### M2 — Manifest pipeline
- `GetDestinyManifest` → download chosen definition tables → cache on disk with
  version check; hash→definition lookup helpers.
- **Done when:** an `itemHash` resolves to a human-readable name/icon/tier offline.

### M3 — First end-to-end read tool
- `get_vault`: GetProfile(102) → manifest-resolve → grouped summary.
- Proves the whole pipeline: auth → API → manifest join → shaping → MCP output.

### M4 — Fill out the tool surface
- Add the remaining tools from §4, each with recorded-fixture tests for shaping.

### M5 — Hardening
- Rate-limit / `ErrorCode` handling, token-expiry edge cases, caching of profile
  responses, README setup/auth docs, CI (lint + tests).

## 7. Key risks & decisions to lock early

1. **Token storage location & encryption** — local file (dev) vs OS keyring vs
   encrypted-at-rest. Affects M1. *Recommend:* encrypted local file for v1.
2. **Manifest footprint** — full SQLite manifest is large; prefer fetching only the
   needed JSON component tables to keep the install light.
3. **Single-user vs multi-user** — plan assumes one signed-in user. Multi-account
   support would change the token store and tool signatures; defer unless needed.
4. **Transport** — **Decided: local stdio.** Targets local desktop MCP clients and
   makes OAuth simple via a loopback redirect. Code stays transport-agnostic so
   HTTP/SSE can be added later if a hosted deployment is ever needed.

## 8. Immediate next step

With this plan approved, the natural first action is **M0 + M1 scaffold**: stand up
the `FastMCP` server, wire `pyproject.toml`, and implement the OAuth flow against a
registered Bungie app so we can pull a real token. Manifest (M2) and the first
`get_vault` tool (M3) follow.

---

### Sources
- [Bungie.net API portal](https://bungie-net.github.io/)
- [Bungie OAuth Documentation (wiki)](https://github.com/Bungie-net/api/wiki/OAuth-Documentation)
- [Bungie API Scopes (wiki)](https://github.com/Bungie-net/api/wiki/Scopes)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Build an MCP server (docs)](https://modelcontextprotocol.io/docs/develop/build-server)
