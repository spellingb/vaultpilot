import type { InventoryItem, ProfileSummary } from "../domain/types.js";

export interface ProfileService {
  getProfile(): Promise<ProfileSummary>;
  getVaultItems(limit: number): Promise<InventoryItem[]>;
  getCharacterInventory(characterId: string, limit: number): Promise<InventoryItem[]>;
  getCurrencies(): Promise<Array<{ name: string; quantity: number }>>;
  getQuestsBounties(limit: number): Promise<Array<{ id: string; name: string; status: string }>>;
}

const MOCK_PROFILE: ProfileSummary = {
  account: {
    membershipType: "bungie",
    membershipId: "4611686018469271295",
    displayName: "MockGuardian"
  },
  characters: [
    { characterId: "2305843009991000001", classType: "warlock", lightLevel: 2010 },
    { characterId: "2305843009991000002", classType: "hunter", lightLevel: 2008 }
  ],
  retrievedAt: new Date().toISOString()
};

const MOCK_ITEMS: InventoryItem[] = [
  {
    itemInstanceId: "1001",
    itemHash: 123,
    name: "Mock Hand Cannon",
    bucket: "Kinetic Weapons",
    quantity: 1,
    power: 2009,
    location: "vault"
  },
  {
    itemInstanceId: "1002",
    itemHash: 124,
    name: "Mock Chest Armor",
    bucket: "Chest Armor",
    quantity: 1,
    power: 2005,
    location: "character",
    characterId: "2305843009991000001"
  }
];

export class MockProfileService implements ProfileService {
  async getProfile(): Promise<ProfileSummary> {
    return { ...MOCK_PROFILE, retrievedAt: new Date().toISOString() };
  }

  async getVaultItems(limit: number): Promise<InventoryItem[]> {
    return MOCK_ITEMS.filter((item) => item.location === "vault").slice(0, limit);
  }

  async getCharacterInventory(characterId: string, limit: number): Promise<InventoryItem[]> {
    return MOCK_ITEMS.filter((item) => item.characterId === characterId).slice(0, limit);
  }

  async getCurrencies(): Promise<Array<{ name: string; quantity: number }>> {
    return [
      { name: "Glimmer", quantity: 250000 },
      { name: "Legendary Shards", quantity: 2112 }
    ];
  }

  async getQuestsBounties(limit: number): Promise<Array<{ id: string; name: string; status: string }>> {
    return [
      { id: "q1", name: "Complete Vanguard Ops", status: "in_progress" },
      { id: "b1", name: "Defeat combatants with Arc", status: "not_started" }
    ].slice(0, limit);
  }
}
