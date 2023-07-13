from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self

from src.engine.events_enum import Events
from src.entities.item.items import HealingPotion

if TYPE_CHECKING:
    from src.entities.entity import Entity

from src.entities.item.inventory_item import Consumable, InventoryItem

Event = dict[str, Any]


class Inventory:
    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() if item else None for item in self.items],
        }

    def __init__(self, owner: Entity, capacity: int = 0) -> None:
        self.owner = owner
        self._capacity = capacity
        self.items: list = [None for _ in range(self.capacity)]

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, value):
        self._capacity = value
        while len(self.items) < self.capacity:
            self.items.append(None)

    def add_item_to_inventory(self, item: InventoryItem) -> list[Event]:
        results = []

        added_to_inventory = False
        for i in range(self.capacity):
            if self.items[i] is None:
                self.items[i] = item
                added_to_inventory = True
                break

        if not added_to_inventory:
            results.append({Events.MESSAGE: "Inventory is Full!"})
        else:
            item.on_add_to_inventory(self)
            results.append({Events.MESSAGE: f"{item.name} added to inventory."})

        return results

    def __contains__(self, item: InventoryItem) -> bool:
        return item in self.items

    def remove_item(self, item):
        if item in self:
            item_idx = self.items.index(item)
            self.items[item_idx] = None

    def consumables(self) -> tuple[Consumable, ...]:
        return tuple(item for item in self.items if isinstance(item, Consumable))
