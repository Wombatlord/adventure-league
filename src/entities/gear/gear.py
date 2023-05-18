from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from src.entities.combat.modifiable_stats import ModifiableStats
from src.entities.combat.stats import EquippableItemStats

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.entities.gear.equippable_item import EquippableItem


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: EquippableItem) -> None:
        ...


class Gear:
    weapon: EquippableItem
    helmet: EquippableItem
    body: EquippableItem

    _equippable_slots = (
        "_weapon",
        "_helmet",
        "_body",
    )

    __slots__ = (
        "owner",
        "base_equipped_stats",
        "modifiable_equipped_stats",
        *_equippable_slots,
    )

    def to_dict(self) -> dict:
        return {
            "weapon": self.weapon.to_dict() if self.weapon else None,
            "helmet": self.helmet.to_dict() if self.helmet else None,
            "body": self.body.to_dict() if self.body else None,
        }

    def __init__(self, owner: Fighter, weapon=None, helmet=None, body=None) -> None:
        self.owner = owner
        self._weapon = weapon
        self._helmet = helmet
        self._body = body
        self.base_equipped_stats = EquippableItemStats()
        self.modifiable_equipped_stats = ModifiableStats(
            EquippableItemStats, self.base_equipped_stats
        )

    @property
    def weapon(self):
        return self._weapon

    @property
    def helmet(self):
        return self._helmet

    @property
    def body(self):
        return self._body

    def update_stats(self, item):
        self.base_equipped_stats += item.stats
        self.modifiable_equipped_stats._base_stats += item.stats
        self.modifiable_equipped_stats.set_modifiers(item.equipment_modifiers())

    def item_in_slot(self, slot) -> EquippableItem | None:
        if slot not in self._equippable_slots:
            return None
        return getattr(self, slot, None)

    def is_equipped(self, item: EquippableItem) -> bool:
        return self.item_in_slot(item.slot) is item

    def equip_item(self, item: EquippableItem, storage: Storage = None):
        slot = item.slot
        if slot not in self._equippable_slots:
            raise ValueError(f"Cannot equip item {item} in slot {slot}")

        self.unequip(slot, storage)
        item.on_equip(self.owner)

        match slot:
            case "_weapon":
                self._weapon = item
            case "_helmet":
                self._helmet = item
            case "_body":
                self._body = item

        self.update_stats(item)

    def unequip(self, slot: str, storage: Storage | None = None):
        if prev_item := self.item_in_slot(slot):
            prev_item.unequip()
            match prev_item.slot:
                case "_weapon":
                    self._weapon = None
                case "_helmet":
                    self._helmet = None
                case "_body":
                    self._body = None
            # Update the aggregation of equippable stats & modifiers
            self.base_equipped_stats -= prev_item.stats
            self.modifiable_equipped_stats._base_stats -= prev_item.stats

            # Remove any affixes that are associated to the item being unequipped
            for affix in prev_item._equippable_item_affixes:
                self.modifiable_equipped_stats.remove(affix.modifier)
                

                
            if storage is not None:
                storage.store(prev_item)
