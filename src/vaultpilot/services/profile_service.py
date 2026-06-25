"""Profile/inventory service protocol + a stateful mock.

The mock holds a small in-memory inventory and supports the write operations
(transfer/equip) so the read + act tool surface can be exercised end to end
without touching Bungie. Writes mutate the mock's state and report the
before/after location so tools can echo a confirmation.
"""

from __future__ import annotations

from typing import Protocol

from ..domain import (
    AccountRef,
    CharacterSummary,
    InventoryItem,
    ProfileSummary,
)
from ..envelope import NotFoundError

_RETRIEVED_AT = "2026-06-25T00:00:00Z"  # fixed in mock for deterministic tests

_WARLOCK = "2305843009991000001"
_HUNTER = "2305843009991000002"


def _mock_profile() -> ProfileSummary:
    return ProfileSummary(
        account=AccountRef(
            membership_type="steam",
            membership_id="4611686018469271295",
            display_name="MockGuardian",
        ),
        characters=[
            CharacterSummary(character_id=_WARLOCK, class_type="warlock", light_level=2010),
            CharacterSummary(character_id=_HUNTER, class_type="hunter", light_level=2008),
        ],
        retrieved_at=_RETRIEVED_AT,
    )


def _mock_items() -> list[InventoryItem]:
    return [
        InventoryItem(
            item_instance_id="1001", item_hash=123, name="Mock Hand Cannon",
            bucket="Kinetic Weapons", quantity=1, power=2009, location="vault",
        ),
        InventoryItem(
            item_instance_id="1002", item_hash=124, name="Mock Chest Armor",
            bucket="Chest Armor", quantity=1, power=2005, location="character",
            character_id=_WARLOCK, equipped=True,
        ),
        InventoryItem(
            item_instance_id="1003", item_hash=125, name="Mock Pulse Rifle",
            bucket="Energy Weapons", quantity=1, power=2007, location="character",
            character_id=_HUNTER, equipped=False,
        ),
    ]


class ProfileService(Protocol):
    def get_profile(self) -> ProfileSummary: ...
    def get_vault_items(self, limit: int) -> list[InventoryItem]: ...
    def get_character_inventory(self, character_id: str, limit: int) -> list[InventoryItem]: ...
    def get_currencies(self) -> list[dict]: ...
    def get_quests_bounties(self, limit: int) -> list[dict]: ...
    def transfer_item(self, item_instance_id: str, destination: str,
                       character_id: str | None) -> dict: ...
    def equip_item(self, item_instance_id: str, character_id: str) -> dict: ...


class MockProfileService:
    def __init__(self) -> None:
        self._items = _mock_items()

    # --- reads ---
    def get_profile(self) -> ProfileSummary:
        return _mock_profile()

    def get_vault_items(self, limit: int) -> list[InventoryItem]:
        return [i for i in self._items if i.location == "vault"][:limit]

    def get_character_inventory(self, character_id: str, limit: int) -> list[InventoryItem]:
        return [i for i in self._items if i.character_id == character_id][:limit]

    def get_currencies(self) -> list[dict]:
        return [
            {"name": "Glimmer", "quantity": 250000},
            {"name": "Legendary Shards", "quantity": 2112},
        ]

    def get_quests_bounties(self, limit: int) -> list[dict]:
        return [
            {"id": "q1", "name": "Complete Vanguard Ops", "status": "in_progress"},
            {"id": "b1", "name": "Defeat combatants with Arc", "status": "not_started"},
        ][:limit]

    # --- writes (read + act) ---
    def _find(self, item_instance_id: str) -> InventoryItem:
        for item in self._items:
            if item.item_instance_id == item_instance_id:
                return item
        raise NotFoundError(f"No item with instance id {item_instance_id}.")

    def transfer_item(self, item_instance_id: str, destination: str,
                      character_id: str | None) -> dict:
        item = self._find(item_instance_id)
        before = {"location": item.location, "character_id": item.character_id}
        if destination == "vault":
            item.location = "vault"
            item.character_id = None
            item.equipped = False
        else:  # destination == "character"
            item.location = "character"
            item.character_id = character_id
        after = {"location": item.location, "character_id": item.character_id}
        return {"item_instance_id": item.item_instance_id, "name": item.name,
                "before": before, "after": after}

    def equip_item(self, item_instance_id: str, character_id: str) -> dict:
        item = self._find(item_instance_id)
        before = {"equipped": item.equipped, "character_id": item.character_id}
        item.location = "character"
        item.character_id = character_id
        item.equipped = True
        after = {"equipped": item.equipped, "character_id": item.character_id}
        return {"item_instance_id": item.item_instance_id, "name": item.name,
                "before": before, "after": after}
