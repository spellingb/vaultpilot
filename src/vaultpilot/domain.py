"""Shared domain models for the assistant-facing tool surface.

These are deliberately compact and decoupled from raw Bungie response shapes.
The normalization layer (M5) will map Bungie JSON onto these; for now the mock
services populate them directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MembershipType = Literal["xbox", "playstation", "steam", "epic", "bungie"]
ClassType = Literal["titan", "hunter", "warlock"]
ItemLocation = Literal["vault", "character"]
RecommendationCategory = Literal["vault_hygiene", "power_progression", "objective_priorities"]


class AccountRef(BaseModel):
    membership_type: MembershipType
    membership_id: str
    display_name: str


class CharacterSummary(BaseModel):
    character_id: str
    class_type: ClassType
    light_level: int


class ProfileSummary(BaseModel):
    account: AccountRef
    characters: list[CharacterSummary]
    retrieved_at: str


class InventoryItem(BaseModel):
    item_instance_id: str
    item_hash: int
    name: str
    bucket: str
    quantity: int
    power: int | None
    location: ItemLocation
    character_id: str | None = None
    equipped: bool = False


class Recommendation(BaseModel):
    id: str
    category: RecommendationCategory
    title: str
    why: str
    evidence: list[str]
    confidence: float
    safety_notes: list[str]
