import type { Recommendation } from "../domain/types.js";

export interface RecommendationEngine {
  getRecommendations(limit: number): Promise<Recommendation[]>;
}

export class MockRecommendationEngine implements RecommendationEngine {
  async getRecommendations(limit: number): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [
      {
        id: "rec-001",
        category: "vault_hygiene",
        title: "Review duplicate hand cannons",
        why: "You have 4 rolls with overlapping perk columns.",
        evidence: ["4 items in Kinetic Weapons with same archetype", "2 have lower power and no unique perks"],
        confidence: 0.77,
        safetyNotes: ["Candidate for evaluation", "No action executed by VaultPilot"]
      },
      {
        id: "rec-002",
        category: "power_progression",
        title: "Run Pinnacle activities on Warlock first",
        why: "Your Warlock has the highest baseline and benefits most from early pinnacle drops.",
        evidence: ["Warlock 2010, Hunter 2008", "2 Pinnacle milestones available"],
        confidence: 0.81,
        safetyNotes: ["Prioritization suggestion only"]
      }
    ];

    return recommendations.slice(0, limit);
  }
}
