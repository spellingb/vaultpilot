import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace"]).default("info"),
  MCP_SERVER_NAME: z.string().default("vaultpilot"),
  MCP_SERVER_VERSION: z.string().default("0.1.0"),
  OAUTH_CALLBACK_PORT: z.coerce.number().int().min(1024).max(65535).default(8787),
  OAUTH_CALLBACK_HOST: z.string().default("127.0.0.1")
});

export type Env = z.infer<typeof envSchema>;

export function parseEnv(input: NodeJS.ProcessEnv = process.env): Env {
  return envSchema.parse(input);
}
