import pino, { type Logger, type LoggerOptions } from "pino";
import type { Env } from "../config/env.js";

export function createLogger(env: Env): Logger {
  const options: LoggerOptions = {
    name: "vaultpilot",
    level: env.LOG_LEVEL,
    redact: {
      paths: [
        "req.headers.authorization",
        "authorization",
        "accessToken",
        "refreshToken",
        "token",
        "secrets.*"
      ],
      censor: "[REDACTED]"
    },
    hooks: {
      logMethod(args, method) {
        const scrubbed = args.map((arg) => {
          if (typeof arg === "string") {
            return arg
              .replace(/Bearer\s+[A-Za-z0-9\-._~+/]+=*/g, "Bearer [REDACTED]")
              .replace(/refresh_token=[^&\s]+/g, "refresh_token=[REDACTED]");
          }
          return arg;
        });
        if (scrubbed.length === 0) {
          method.call(this, {});
          return;
        }
        (method as (...methodArgs: unknown[]) => void).apply(this, scrubbed);
      }
    }
  };

  return pino(options);
}
