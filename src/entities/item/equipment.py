from __future__ import annotations

import abc
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.entities.item.equippable import Equippable
    from src.entities.combat.fighter import Fighter


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

    def unequip(self, slot: str, storage: Storage):
        if prev_item := self.item_in_slot(slot):
            prev_item.unequip()
            storage.store(prev_item)
