import { describe, expect, it } from "vitest";
import { characterInventoryInputSchema, recommendationsInputSchema, vaultItemsInputSchema } from "../src/mcp/schemas.js";

describe("tool schemas", () => {
  it("applies defaults for vault_items_get", () => {
    const parsed = vaultItemsInputSchema.parse({ requestId: "r1" });
    expect(parsed.detail).toBe("summary");
    expect(parsed.limit).toBe(25);
  });

  it("rejects out-of-range limits", () => {
    expect(() => vaultItemsInputSchema.parse({ requestId: "r1", limit: 101 })).toThrow();
  });

  it("requires characterId for character inventory", () => {
    expect(() => characterInventoryInputSchema.parse({ requestId: "r1" })).toThrow();
  });

  it("supports recommendations detail and limit", () => {
    const parsed = recommendationsInputSchema.parse({ requestId: "r1", detail: "full", limit: 2 });
    expect(parsed.detail).toBe("full");
    expect(parsed.limit).toBe(2);
  });
});
