# VaultPilot MVP Assumptions

## Core Technical Assumptions
- Runtime is modern Node.js LTS with TypeScript strict mode.
- MCP SDK is standardized on `@modelcontextprotocol/sdk` stable v1 imports only.
- Local stdio is the only transport target for MVP.
- MVP remains read-only end-to-end, including tool contracts and service boundaries.

## OAuth and Scope Assumptions
- Bungie OAuth app credentials are supplied via environment variables.
- OAuth completion happens through a localhost callback handler as the primary path.
- Bungie OAuth requests do not send a dynamic `scope` parameter.
- Allowed MVP capabilities are limited to read access equivalent to:
  - `ReadBasicUserProfile`
  - `ReadDestinyInventoryAndVault`
- No Bungie write scopes are requested or processed in MVP.

## Data and Storage Assumptions
- Initial token persistence uses a local filesystem implementation with restrictive file permissions where supported.
- Manifest caching starts as local file-based cache with metadata (`version`, `updatedAt`, `ttl`, optional checksum).
- Stale-while-revalidate and explicit refresh are acceptable for MVP manifest freshness.
- MVP supports a single configured account context at a time.

## API and Normalization Assumptions
- Bungie response shapes can be partial or variant; runtime validation and graceful fallback are required.
- The MVP `GetProfile` component preset includes only minimum required components for planned tools.
- `ItemReusablePlugs` is opt-in only (feature-flag/tool-option gate), not default.
- Normalized outputs must preserve provenance metadata and explicit missing/unknown indicators.

## Tooling and Payload Assumptions
- MCP tools are intentionally split into narrow endpoints for predictable payloads.
- All list-heavy tools default to `detail="summary"` and only expand on `detail="full"`.
- Pagination (`limit`, `cursor`) and hard response caps are mandatory for large data sets.
- Recommendation outputs are advisory and conservative, with confidence and evidence required.

## Recommendation Language Constraints
- Recommendation categories are:
  - `vault_hygiene`
  - `power_progression`
  - `objective_priorities`
- Output language must avoid destructive terms (for example: `dismantle`, `delete`, `trash`, `junk`, `scrap`, `purge`).
- Preferred phrasing is evaluative and non-actional (for example: "consider reviewing", "candidate for evaluation").

## Explicit MVP Non-Goals (Assumed Stable)
- No web dashboard.
- No item movement or transfer operations.
- No equip/unequip.
- No lock/unlock.
- No loadout apply.
- No dismantle operations.
- No DIM inventory integration.
- No multi-tenant auth broker or cloud deployment in MVP.

## Open Decisions to Resolve Before/During Implementation
- Exact numeric defaults for payload limits and per-tool max response size.
- Required minimum Destiny data breadth for first recommendation quality bar.
- Final cross-platform filesystem path conventions for token and manifest storage.
- Whether multi-account support should remain post-MVP or be introduced earlier.

## Post-MVP Extension Guardrail
- Future DIM integration, if added, is metadata-only (tags/notes/loadout descriptors), not inventory state sync.
