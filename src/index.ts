import { parseEnv } from "./config/env.js";
import { createLogger } from "./logger/index.js";
import { MockAuthService } from "./services/auth-service.js";
import { MockProfileService } from "./services/profile-service.js";
import { MockRecommendationEngine } from "./services/recommendation-engine.js";
import { startStdioServer } from "./server/stdio.js";

async function main(): Promise<void> {
  const env = parseEnv();
  const logger = createLogger(env);

  const context = {
    authService: new MockAuthService(),
    profileService: new MockProfileService(),
    recommendationEngine: new MockRecommendationEngine()
  };

  await startStdioServer(context, logger);
}

main().catch((error: unknown) => {
  const env = parseEnv();
  const logger = createLogger(env);
  logger.error({ err: error }, "VaultPilot startup failed");
  process.exitCode = 1;
});
