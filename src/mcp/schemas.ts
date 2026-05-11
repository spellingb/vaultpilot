import { z } from "zod";

export const detailSchema = z.enum(["summary", "full"]).default("summary");
export const requestIdSchema = z.string().min(1).default("req-local");
export const limitSchema = z.coerce.number().int().min(1).max(100).default(25);
export const cursorSchema = z.string().optional();

export const authStartInputSchema = z.object({
  requestId: requestIdSchema
});

export const authStatusInputSchema = z.object({
  requestId: requestIdSchema
});

export const authLogoutInputSchema = z.object({
  requestId: requestIdSchema
});

export const manifestStatusInputSchema = z.object({
  requestId: requestIdSchema
});

export const playerProfileInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema
});

export const vaultItemsInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema,
  limit: limitSchema,
  cursor: cursorSchema
});

export const characterInventoryInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema,
  characterId: z.string().min(1),
  limit: limitSchema,
  cursor: cursorSchema
});

export const currenciesInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema
});

export const questsBountiesInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema,
  limit: limitSchema,
  cursor: cursorSchema
});

export const recommendationsInputSchema = z.object({
  requestId: requestIdSchema,
  detail: detailSchema,
  limit: limitSchema
});
