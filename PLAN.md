# VaultPilot — Implementation Plan

> An MCP server that lets AI assistants **analyze and manage** a player's Destiny 2
> inventory, vault, quests, currencies, triumphs, and weekly priorities using the
> official [Bungie.net API](https://bungie-net.github.io/) — reading private data
> *and* performing guarded item transfers/equips on the user's behalf.

**Status:** Greenfield (Python). The repo contains `README.md`, this plan, and the
credential scaffolding (`.env.example`, `.gitignore`). There is no Python connector
code yet — this document is the build plan, not a record of work done.

> **A note on the `feat/mock-foundation-phase1-2` branch.** That branch holds a
> well-built *TypeScript* mock-first foundation (10 tool contracts, tests, two strong
> design docs). We are **not building on it** — we stay Python/FastMCP — but we have
> **harvested its design**: the response envelope, the response-size policy, the
> mock-first phasing, the recommendation guardrails, and the OAuth scope correction
> below all come from it. The branch stays on the remote as a design reference.

- **Language / runtime:** Python (3.11+)
- **MCP framework:** [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`FastMCP`)
- **Transport:** local **stdio** (decided — see §7)
- **Auth:** Full Bungie OAuth2 (Authorization Code flow) so the server reads the
  signed-in user's *own* private inventory/vault **and** can move/equip their items.
- **Scope:** **Read + act.** VaultPilot reads *and* performs item transfers and
  equips. Write actions are guarded, reversible-by-nature, and never destructive
  (see §12). Bungie scopes required: `ReadDestinyInventoryAndVault` **and**
  `MoveEquipDestinyItems`.

---

## 1. Why "not functional" today

There is nothing to debug — the connector simply hasn't been built in Python.
Everything below is net-new. The clean slate is an advantage: we can set the auth,
manifest, and safety foundations correctly the first time, which is where most
Destiny-API projects go wrong. We also start from a validated design (harvested from
the TS branch) rather than a blank page.

## 2. The three hard problems (where the time actually goes)

### 2.1 Bungie OAuth2 — not just an API key
Reading a player's private inventory/vault — and moving/equipping items — requires an
OAuth2 **access token**. An API key alone only unlocks public + manifest data. Key
facts (verified against current Bungie docs):

- **Authorize URL:** `https://www.bungie.net/en/OAuth/Authorize`
- **Token URL:** `https://www.bungie.net/Platform/App/OAuth/Token/`
- Every API request must also send the `X-API-Key` header.
- **Scopes are fixed by the Bungie app's checkboxes, NOT passed in the authorize
  URL.** Bungie does *not* accept a dynamic `scope` query parameter — the granted
  scope is whatever you ticked when registering the app. (So the `BUNGIE_OAUTH_SCOPE`
  value in `.env` is documentation only; it is never sent on the wire.)
- Scopes we need: **`ReadDestinyInventoryAndVault`** (covers `profileCurrencies`,
  `profileInventory`, `characterInventories`, vendor receipts, milestones,
  progression) **and `MoveEquipDestinyItems`** (transfer/equip/lock).
- **Access token lives ~1 hour**; refresh via the token endpoint.
- **Refresh token lives up to 90 days**, renewed for another 90 on each refresh, to a
  hard 1-year ceiling — after which the user must re-authorize.
- Apps can be **Confidential** (has a client secret → use HTTP Basic auth on the token
  endpoint) or **Public**. We register a **Confidential** app.

**Design implication:** we need durable, secure token storage with transparent
refresh-on-expiry. This is the single biggest piece of the project.

### 2.2 The Destiny Manifest
The API returns items as numeric `itemHash` values, not names. To say *"you have 3
Gjallarhorns in your vault"* we must join those hashes against the **Destiny
Manifest** — a large, versioned set of definition tables (item, stat, class,
record/triumph, milestone, bucket, etc.).

- Fetch via `GET /Destiny2/Manifest/`, which returns versioned paths to the JSON
  world-content and the mobile SQLite content.
- Large and changes on each game patch, so it must be **cached on disk and
  version-checked**, not downloaded per request. Cache metadata: `version`,
  `updatedAt`, `ttl`, optional checksum; serve stale-while-revalidate.
- We only need a subset of definition tables for the features in scope.

### 2.3 MCP tool-surface design
Raw Bungie `GetProfile` responses are deeply nested and enormous. The value VaultPilot
adds is **shaping** that data into compact, LLM-friendly tool outputs so an assistant
can reason without drowning in JSON. Outputs are manifest-resolved (names, not hashes),
summarized, and carry provenance (`sourceComponent`, `retrievedAt`).

---

## 3. Core data flow

```
AI assistant ──(MCP/stdio)──▶ VaultPilot server
                                  │
                                  ├─ ensure valid OAuth token (refresh if stale)
                                  ├─ resolve membershipType + destinyMembershipId
                                  │     via GetMembershipsForCurrentUser
                                  ├─ READ:  GET /Destiny2/{type}/Profile/{id}/?components=...
                                  ├─ ACT:   POST TransferItem / EquipItem  (guarded)
                                  ├─ join itemHashes ▶ cached Manifest definitions
                                  └─ shape ▶ compact JSON envelope ▶ back to assistant
```

Key Bungie endpoints:
- `GetMembershipsForCurrentUser` — find the player's platform + membership id.
- `Destiny2.GetProfile` with **components** (the read workhorse):
  - `100` Profiles, `200` Characters
  - `102` ProfileInventories (**the vault**)
  - `201` CharacterInventories, `205` CharacterEquipment
  - `103/105` Currencies / platform silver, `104` ProfileProgression
  - `202` CharacterProgressions (weekly milestones / "priorities")
  - `900` Records (**triumphs**), `1100` Metrics
- `Destiny2.GetDestinyManifest` — manifest version + paths.
- **Write endpoints** (require `MoveEquipDestinyItems`):
  - `Destiny2.TransferItem` — vault ⇄ character.
  - `Destiny2.EquipItem` / `Destiny2.EquipItems` — equip gear on a character.
  - `Destiny2.SetItemLockState` — lock/unlock (later).

> Note: component numbers and manifest shapes shift over time — confirm against the
> live [API spec](https://bungie-net.github.io/) at implementation time.

---

## 4. Proposed MCP tools

Every tool returns a consistent **envelope** (harvested from the TS branch):

```
{ "data": <payload>, "meta": { "requestId", "detail", ... }, "warnings": [ ... ] }
```

**Response-size policy (mandatory for list-heavy tools):** default
`detail="summary"`, optional `detail="full"`; `limit`/`cursor` pagination; hard cap
`limit <= 100` with truncation noted in `meta`.

### Auth & system
| Tool | Purpose |
|------|---------|
| `auth_start` | Return Bungie authorize URL + state nonce; ensure local callback listener is up. |
| `auth_status` | Current auth state (authenticated / expired / refreshing / missing) with masked account info. |
| `auth_logout` | Clear local token state. |
| `manifest_status_get` | Manifest cache version, age, staleness. |

### Read (require `ReadDestinyInventoryAndVault`)
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
| `recommendations_get` | Conservative, confidence-gated, advisory suggestions (see §12). |

### Act (require `MoveEquipDestinyItems`) — guarded, see §12
| Tool | Purpose |
|------|---------|
| `transfer_item` | Move an item vault ⇄ character (and between characters via vault). |
| `equip_item` | Equip an item already on a character. |

Read tools return a compact dict (names, counts, progress %), never raw Bungie JSON.
Write tools echo back the resolved item name + before/after location so the assistant
can confirm what changed.

## 5. Project layout

```
vaultpilot/
├── README.md
├── PLAN.md                      ← this file
├── pyproject.toml               ← deps: mcp, httpx, pydantic, (aiosqlite)
├── .env.example                 ← API key, client id/secret, redirect, scopes
├── .env                         ← real secrets (gitignored)
├── src/vaultpilot/
│   ├── __init__.py
│   ├── server.py                ← FastMCP instance + tool registration
│   ├── config.py                ← env/settings loading (pydantic-settings)
│   ├── envelope.py              ← {data, meta, warnings} helper + error taxonomy
│   ├── auth/
│   │   ├── oauth.py             ← authorize URL, local callback, code→token, refresh
│   │   └── token_store.py       ← secure persistence of tokens
│   ├── bungie/
│   │   ├── client.py            ← httpx client; X-API-Key; auto refresh; retry/backoff
│   │   ├── profile.py           ← GetProfile component calls
│   │   ├── actions.py           ← TransferItem / EquipItem (write ops)
│   │   └── manifest.py          ← download/cache/version-check + hash lookups
│   ├── services/                ← swappable interfaces (mock-first, see §15)
│   │   ├── auth_service.py
│   │   ├── profile_service.py
│   │   └── recommendation_engine.py
│   ├── tools/                   ← one module per MCP tool (thin: validate → call → shape)
│   └── shaping.py               ← raw Bungie JSON → compact LLM-friendly dicts
└── tests/
    ├── test_manifest.py
    ├── test_shaping.py          ← against recorded fixtures (no live API)
    ├── test_oauth.py            ← token refresh logic
    └── test_tools.py            ← handler contracts against mocked services
```

## 6. Error taxonomy

Normalize Bungie failures into internal categories (harvested from TS branch) so tools
fail predictably: `AuthError`, `RateLimitError`, `UpstreamError`, `NotFoundError`.
Surface them in the envelope's `warnings`/error channel; never leak raw tokens.

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
5. **Write-action safety** — now that we move/equip, a wrong call mutates the user's
   game state. Mitigations in §12 are mandatory, not optional.

## 8. Milestones

### M0 — Project scaffold *(no Bungie calls)*
- `pyproject.toml`, package skeleton, `FastMCP` server that starts over stdio.
- One stub tool (`ping`) to confirm an MCP client can connect.
- **Done when:** server registers and responds in an MCP client.

### M1 — Mock-first tool surface *(no Bungie calls)*
- Implement all §4 tools against **mocked services** (auth/profile/recommendation),
  with the full envelope + response-size policy + recommendation guardrails.
- Handler contract tests (mirrors the TS branch's Phase 1-2).
- **Done when:** every tool returns a well-shaped mock envelope and tests pass.

### M2 — Bungie OAuth2
- Register a Confidential app on Bungie.net (read **+** move/equip scopes); capture
  key/id/secret/redirect.
- Authorization-code flow: build authorize URL, run a tiny local redirect handler to
  capture `code`, exchange for tokens.
- Token store with automatic refresh-on-expiry; handle the 90-day/1-year limits.
- **Done when:** server holds a valid access token and refreshes transparently.

### M3 — Manifest pipeline
- `GetDestinyManifest` → download chosen definition tables → cache on disk with
  version check; hash→definition lookup helpers.
- **Done when:** an `itemHash` resolves to a human-readable name/icon/tier offline.

### M4 — First end-to-end read tool
- Swap `get_vault`'s mock for real: GetProfile(102) → manifest-resolve → grouped
  summary. Proves auth → API → manifest join → shaping → MCP output.

### M5 — Fill out the read surface
- Wire the remaining read tools from §4 to live data, each with fixture-based tests.

### M6 — Write actions
- `transfer_item`, `equip_item` against `TransferItem`/`EquipItem`, behind the §12
  safety guards. Integration-test against a throwaway character first.

### M7 — Hardening
- Rate-limit / `ErrorCode` handling, token-expiry edges, profile-response caching,
  README setup/auth docs, CI (lint + tests).

## 9. Manifest caching

`ManifestCache` with versioned metadata + component access. Local file cache with
index (`version`, `updatedAt`, `ttl`, checksum). Fetch-on-miss + stale-while-revalidate;
explicit refresh path. Integrity check before serving; safe fallback (limited output +
warning) when the manifest is unavailable.

## 10. Data normalization

Stable domain models separate raw Bungie shapes from tool outputs. Resolve hashes via
the manifest layer; keep provenance (`sourceComponent`, `retrievedAt`); mark
unknown/missing fields explicitly rather than silently dropping; produce compact
`summary` views first, enrich on `detail="full"`.

## 11. Recommendation engine

Conservative, deterministic rules (advisory only). Categories: `vault_hygiene`,
`power_progression`, `objective_priorities`. Each recommendation carries `why`,
`evidence`, `confidence`, `safetyNotes`, `category`; emitted only above a confidence
threshold with required evidence, else `"insufficient_data"`.

## 12. Safety & write-action guardrails

We now perform writes, so safety is first-class:

- **Least-privilege scope:** request only `ReadDestinyInventoryAndVault` +
  `MoveEquipDestinyItems`. No clan/admin scopes.
- **No destructive operations, ever:** VaultPilot will **not** dismantle, delete,
  shard, or discard items — only transfer/equip/lock, all reversible. No
  `SetItemLockState` to delete; no vendor-sell.
- **Non-destructive language** in all recommendation/text output: avoid
  `dismantle`/`delete`/`trash`/`junk`/`scrap`/`purge`; prefer "consider reviewing",
  "candidate for evaluation". (Harvested guardrail from the TS branch.)
- **Write tools never auto-fire:** `transfer_item`/`equip_item` act only on explicit,
  fully-specified instructions (item instance id + destination), and the response
  echoes the before/after state for confirmation. Recommendations are advisory and
  never execute actions themselves.
- **Secrets:** env vars only; token values redacted in logs; token file locked to
  owner read/write where the OS supports it.
- **Read-only enforcement** still applies to every read tool by construction.

## 13. Test plan

- **Unit:** schema validation, normalization mappers, recommendation rules, cache
  policy, response-size policy (`summary` vs `full`, limit bounds, cursor metadata).
- **Integration:** tool handlers against mocked token store / manifest / Bungie API;
  OAuth localhost callback flow; error propagation (rate limit, expired token,
  malformed payload). Write tools tested against a throwaway character.
- **Quality gates:** typecheck/lint/test in CI; critical modules ≥ 80% coverage.

## 14. Mock-first build philosophy

Mirroring the TS branch: build the entire MCP surface against mocked services first
(M0–M1), then swap in real Bungie integration table by table (M2–M6). This lets us
nail the tool contracts and assistant-facing shapes before fighting live-API
variability.

## 15. Immediate next step

With this plan approved, the natural first action is **M0 + M1**: stand up the
`FastMCP` server, wire `pyproject.toml`, and build the full mock-first tool surface
(no credentials needed). OAuth (M2) follows once the Bungie app is registered with
**both** the read and move/equip scopes.

---

### Sources
- [Bungie.net API portal](https://bungie-net.github.io/)
- [Bungie OAuth Documentation (wiki)](https://github.com/Bungie-net/api/wiki/OAuth-Documentation)
- [Bungie API Scopes (wiki)](https://github.com/Bungie-net/api/wiki/Scopes)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Build an MCP server (docs)](https://modelcontextprotocol.io/docs/develop/build-server)
- Design reference: `feat/mock-foundation-phase1-2` branch (TypeScript mock-first foundation)
