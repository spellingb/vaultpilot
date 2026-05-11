export type MembershipType = "xbox" | "playstation" | "steam" | "epic" | "bungie";

export interface AccountRef {
  membershipType: MembershipType;
  membershipId: string;
  displayName: string;
}

export interface CharacterSummary {
  characterId: string;
  classType: "titan" | "hunter" | "warlock";
  lightLevel: number;
}

export interface ProfileSummary {
  account: AccountRef;
  characters: CharacterSummary[];
  retrievedAt: string;
}

export interface InventoryItem {
  itemInstanceId: string;
  itemHash: number;
  name: string;
  bucket: string;
  quantity: number;
  power: number | null;
  location: "vault" | "character";
  characterId?: string;
}

export interface Recommendation {
  id: string;
  category: "vault_hygiene" | "power_progression" | "objective_priorities";
  title: string;
  why: string;
  evidence: string[];
  confidence: number;
  safetyNotes: string[];
}

export interface ToolMeta {
  requestId: string;
  detail: "summary" | "full";
}

export interface ToolEnvelope<TData> {
  data: TData;
  meta: ToolMeta;
  warnings: string[];
}
