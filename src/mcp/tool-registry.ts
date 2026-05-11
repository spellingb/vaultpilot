import type { ZodTypeAny } from "zod";
import type { ToolEnvelope } from "../domain/types.js";
import {
  authLogoutInputSchema,
  authStartInputSchema,
  authStatusInputSchema,
  characterInventoryInputSchema,
  currenciesInputSchema,
  manifestStatusInputSchema,
  playerProfileInputSchema,
  questsBountiesInputSchema,
  recommendationsInputSchema,
  vaultItemsInputSchema
} from "./schemas.js";
import type { AuthService } from "../services/auth-service.js";
import type { ProfileService } from "../services/profile-service.js";
import type { RecommendationEngine } from "../services/recommendation-engine.js";

export interface ToolContext {
  authService: AuthService;
  profileService: ProfileService;
  recommendationEngine: RecommendationEngine;
}

type ToolHandler<TInput, TOutput> = (input: TInput, context: ToolContext) => Promise<ToolEnvelope<TOutput>>;

interface ToolDef<TInput, TOutput> {
  name: string;
  description: string;
  schema: ZodTypeAny;
  handler: ToolHandler<TInput, TOutput>;
}

function envelope<TData>(requestId: string, detail: "summary" | "full", data: TData, warnings: string[] = []) {
  return { data, meta: { requestId, detail }, warnings };
}

export function createToolRegistry() {
  const tools: Array<ToolDef<unknown, unknown>> = [
    {
      name: "auth_start",
      description: "Start mock OAuth flow and return authorization URL.",
      schema: authStartInputSchema,
      handler: async (input, ctx) => {
        const parsed = authStartInputSchema.parse(input);
        const data = await ctx.authService.startAuth();
        return envelope(parsed.requestId, "summary", data);
      }
    },
    {
      name: "auth_status",
      description: "Read current mock auth status.",
      schema: authStatusInputSchema,
      handler: async (input, ctx) => {
        const parsed = authStatusInputSchema.parse(input);
        const data = await ctx.authService.getStatus();
        return envelope(parsed.requestId, "summary", data);
      }
    },
    {
      name: "auth_logout",
      description: "Clear local mock auth state.",
      schema: authLogoutInputSchema,
      handler: async (input, ctx) => {
        const parsed = authLogoutInputSchema.parse(input);
        const data = await ctx.authService.logout();
        return envelope(parsed.requestId, "summary", data);
      }
    },
    {
      name: "manifest_status_get",
      description: "Get mocked manifest cache status.",
      schema: manifestStatusInputSchema,
      handler: async (input) => {
        const parsed = manifestStatusInputSchema.parse(input);
        const data = {
          version: "mock-manifest-v1",
          updatedAt: new Date().toISOString(),
          stale: false
        };
        return envelope(parsed.requestId, "summary", data);
      }
    },
    {
      name: "player_profile_get",
      description: "Return mocked player profile summary.",
      schema: playerProfileInputSchema,
      handler: async (input, ctx) => {
        const parsed = playerProfileInputSchema.parse(input);
        const data = await ctx.profileService.getProfile();
        return envelope(parsed.requestId, parsed.detail, data);
      }
    },
    {
      name: "vault_items_get",
      description: "Return mocked vault items.",
      schema: vaultItemsInputSchema,
      handler: async (input, ctx) => {
        const parsed = vaultItemsInputSchema.parse(input);
        const items = await ctx.profileService.getVaultItems(parsed.limit);
        return envelope(parsed.requestId, parsed.detail, {
          items,
          cursor: null,
          returned: items.length
        });
      }
    },
    {
      name: "character_inventory_get",
      description: "Return mocked character inventory items.",
      schema: characterInventoryInputSchema,
      handler: async (input, ctx) => {
        const parsed = characterInventoryInputSchema.parse(input);
        const items = await ctx.profileService.getCharacterInventory(parsed.characterId, parsed.limit);
        return envelope(parsed.requestId, parsed.detail, {
          characterId: parsed.characterId,
          items,
          cursor: null,
          returned: items.length
        });
      }
    },
    {
      name: "currencies_get",
      description: "Return mocked currency balances.",
      schema: currenciesInputSchema,
      handler: async (input, ctx) => {
        const parsed = currenciesInputSchema.parse(input);
        const data = await ctx.profileService.getCurrencies();
        return envelope(parsed.requestId, parsed.detail, data);
      }
    },
    {
      name: "quests_bounties_get",
      description: "Return mocked quests and bounties.",
      schema: questsBountiesInputSchema,
      handler: async (input, ctx) => {
        const parsed = questsBountiesInputSchema.parse(input);
        const items = await ctx.profileService.getQuestsBounties(parsed.limit);
        return envelope(parsed.requestId, parsed.detail, {
          items,
          cursor: null,
          returned: items.length
        });
      }
    },
    {
      name: "recommendations_get",
      description: "Return mocked conservative recommendations.",
      schema: recommendationsInputSchema,
      handler: async (input, ctx) => {
        const parsed = recommendationsInputSchema.parse(input);
        const data = await ctx.recommendationEngine.getRecommendations(parsed.limit);
        return envelope(parsed.requestId, parsed.detail, data, [
          "Mock recommendations only; no live Bungie data in Phase 1-2."
        ]);
      }
    }
  ];

  return {
    list: () => tools,
    byName: (name: string) => tools.find((tool) => tool.name === name)
  };
}
