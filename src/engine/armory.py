from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: EquippableItem) -> None:
        ...

    @abc.abstractmethod
    def remove(self, item: EquippableItem) -> None:
        ...

    @abc.abstractmethod
    def __contains__(self, item: EquippableItem) -> bool:
        ...


class Armory(Storage):
    weapons: list[EquippableItem]
    armour: list[EquippableItem]

    def __init__(self) -> None:
        self.weapons = []
        self.armour = []
        self.storage = []

    def store(self, item: EquippableItem) -> None:
        self.storage.append(item)

    def remove(self, item: EquippableItem) -> None:
        self.storage.remove(item)

    @property
    def count(self) -> int:
        return len(self.storage)

    def __contains__(self, item: EquippableItem) -> bool:
        return item in self.storage
