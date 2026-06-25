"""Recommendation engine protocol + a mock.

Recommendations are advisory only and confidence-gated. Output must use
non-destructive language (no "dismantle"/"delete"/"trash"/etc.) per the safety
guardrails in PLAN.md §12 — enforced by tests.
"""

from __future__ import annotations

from typing import Protocol

from ..domain import Recommendation

# Words that must never appear in recommendation text (safety guardrail).
BANNED_TERMS = ("dismantle", "delete", "trash", "junk", "scrap", "purge")


class RecommendationEngine(Protocol):
    def get_recommendations(self, limit: int) -> list[Recommendation]: ...


class MockRecommendationEngine:
    def get_recommendations(self, limit: int) -> list[Recommendation]:
        recs = [
            Recommendation(
                id="rec-001",
                category="vault_hygiene",
                title="Review duplicate hand cannons",
                why="You have multiple rolls with overlapping perk columns.",
                evidence=[
                    "4 items in Kinetic Weapons with the same archetype",
                    "2 have lower power and no unique perks",
                ],
                confidence=0.77,
                safety_notes=["Candidate for evaluation", "No action executed by VaultPilot"],
            ),
            Recommendation(
                id="rec-002",
                category="power_progression",
                title="Run pinnacle activities on your Warlock first",
                why="Your Warlock has the highest baseline and benefits most from early pinnacle drops.",
                evidence=["Warlock 2010, Hunter 2008", "2 pinnacle milestones available"],
                confidence=0.81,
                safety_notes=["Prioritization suggestion only"],
            ),
        ]
        return recs[:limit]
