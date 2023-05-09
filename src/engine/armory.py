from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.item.equippable import Equippable


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: Equippable) -> None:
        ...


class Armory(Storage):
    weapons: list[Equippable]
    armour: list[Equippable]

    def __init__(self) -> None:
        self.weapons = []
        self.armour = []

    def store(self, item: Equippable) -> None:
        if item.slot == "weapon":
            self.weapons.append(item)

        else:
            self.armour.append(item)
