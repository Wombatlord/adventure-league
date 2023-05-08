from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Self

from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import FighterStats, StatAffix

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.entities.item.equippable import Equippable, EquippableConfig


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: Equippable) -> None:
        ...


class Equipment:
    weapon: Equippable
    helmet: Equippable
    body: Equippable

    _equippable_slots = (
        "weapon",
        "helmet",
        "body",
    )

    __slots__ = (
        "owner",
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
        self.weapon = weapon
        self.helmet = helmet
        self.body = body

    def item_in_slot(self, slot) -> Equippable | None:
        if slot not in self._equippable_slots:
            return None
        return getattr(self, slot, None)

    def equip_item(self, item: Equippable, storage: Storage = None):
        slot = item.slot
        if slot not in self._equippable_slots:
            raise ValueError(f"Cannot equip item {item} in slot {slot}")

        self.unequip(slot, storage)
        item.on_equip(self.owner)
        setattr(self, slot, item)

    def unequip(self, slot: str, storage: Storage | None = None):
        if prev_item := self.item_in_slot(slot):
            prev_item.unequip()
            if storage is not None:
                storage.store(prev_item)
