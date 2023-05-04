from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Self

from src.entities.combat.attack_types import WeaponAttack
from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import FighterStats
from src.entities.magic.spells import Spell

if TYPE_CHECKING:
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

    def equip_item(self, item: Equippable, storage: Storage):
        slot = item.slot
        if slot not in self._equippable_slots:
            raise ValueError(f"Cannot equip item {item} in slot {slot}")

        self.unequip(slot, storage)
        item.on_equip()
        setattr(self, slot, item)

    def unequip(self, slot: str, storage: Storage):
        if prev_item := self.item_in_slot(slot):
            prev_item.unequip()
            storage.store(prev_item)


class Equippable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_equip(self) -> Self:
        raise NotImplementedError()

    @abc.abstractmethod
    def unequip(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _prepare_attacks(self) -> list[WeaponAttack]:
        raise NotImplementedError()

    @abc.abstractmethod
    def _prepare_spells(self) -> list[Spell]:
        raise NotImplementedError()

    @abc.abstractmethod
    def modifiers(self) -> list[Modifier[FighterStats]]:
        raise NotImplementedError()
