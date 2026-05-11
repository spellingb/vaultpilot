import { describe, expect, it } from "vitest";
import { createToolRegistry } from "../src/mcp/tool-registry.js";
import { MockAuthService } from "../src/services/auth-service.js";
import { MockProfileService } from "../src/services/profile-service.js";
import { MockRecommendationEngine } from "../src/services/recommendation-engine.js";

function createContext() {
  return {
    authService: new MockAuthService(),
    profileService: new MockProfileService(),
    recommendationEngine: new MockRecommendationEngine()
  };
}

describe("mocked tool handlers", () => {
  it("auth_start transitions auth_status to authenticated", async () => {
    const registry = createToolRegistry();
    const context = createContext();
    const authStart = registry.byName("auth_start");
    const authStatus = registry.byName("auth_status");

    expect(authStart).toBeDefined();
    expect(authStatus).toBeDefined();

    await authStart!.handler({ requestId: "req-auth" }, context);
    const status = await authStatus!.handler({ requestId: "req-auth" }, context);
    const statusData = status.data as { state: string };
    expect(statusData.state).toBe("authenticated");
  });

  it("player_profile_get returns profile payload", async () => {
    const registry = createToolRegistry();
    const context = createContext();
    const tool = registry.byName("player_profile_get");
    expect(tool).toBeDefined();

    const result = await tool!.handler({ requestId: "r2", detail: "summary" }, context);
    const data = result.data as { account: { displayName: string } };
    expect(data.account.displayName).toBe("MockGuardian");
  });

  it("recommendations_get returns warnings in mock mode", async () => {
    const registry = createToolRegistry();
    const context = createContext();
    const tool = registry.byName("recommendations_get");
    expect(tool).toBeDefined();

    const result = await tool!.handler({ requestId: "r3", detail: "summary", limit: 1 }, context);
    expect(result.warnings.length).toBeGreaterThan(0);
    const data = result.data as Array<{ category: string }>;
    expect(data[0]?.category).toBe("vault_hygiene");
  });
});
