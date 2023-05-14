from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: EquippableItem) -> None:
        ...


class Armory(Storage):
    weapons: list[EquippableItem]
    armour: list[EquippableItem]

    def __init__(self) -> None:
        self.weapons = []
        self.armour = []

    def store(self, item: EquippableItem) -> None:
        if item.slot == "weapon":
            self.weapons.append(item)

        else:
            self.armour.append(item)
