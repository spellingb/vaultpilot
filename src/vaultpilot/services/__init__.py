"""Service interfaces and their mock-first implementations.

The tool layer depends only on these protocols, so M2+ can swap the mocks for
real Bungie-backed implementations without touching tool code.
"""

from .auth_service import AuthService, MockAuthService
from .profile_service import MockProfileService, ProfileService
from .recommendation_engine import MockRecommendationEngine, RecommendationEngine

__all__ = [
    "AuthService",
    "MockAuthService",
    "ProfileService",
    "MockProfileService",
    "RecommendationEngine",
    "MockRecommendationEngine",
]
