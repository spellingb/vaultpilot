import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { Logger } from "pino";
import { createToolRegistry, type ToolContext } from "../mcp/tool-registry.js";

export function createMcpServer(context: ToolContext, logger: Logger) {
  const server = new McpServer({
    name: "vaultpilot",
    version: "0.1.0"
  });

  const registry = createToolRegistry();
  for (const tool of registry.list()) {
    (server as any).tool(tool.name, tool.description, async (input: unknown) => {
      const result = await (tool.handler as any)(input, context);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result)
          }
        ]
      };
    });
  }

  logger.info({ toolCount: registry.list().length }, "Registered MCP tools");
  return server;
}

export async function startStdioServer(context: ToolContext, logger: Logger): Promise<void> {
  const transport = new StdioServerTransport();
  const server = createMcpServer(context, logger);
  await (server as any).connect(transport);
  logger.info("VaultPilot MCP stdio server started");
}
