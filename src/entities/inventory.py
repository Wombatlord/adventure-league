from typing import TYPE_CHECKING, Optional

from src.entities.entity import Entity

if TYPE_CHECKING:
    from src.engine.engine import Action


class Inventory:
    def __init__(self, capacity: int = 0) -> None:
        self._capacity = 0
        self.capacity = capacity
        self.items: list[Optional[Entity]] = [None for _ in range(self.capacity)]

    def get_capacity(self):
        return self._capacity

    def set_capacity(self, value):
        self._capacity = value
        while len(self.items) < self.capacity:
            self.items.append(None)

    def add_item_to_inventory(self, item: Entity) -> list["Action"]:
        results = []

        added_to_inventory = False
        for i in range(self.capacity):
            if self.items[i] is None:
                self.items[i] = item
                added_to_inventory = True
                break

        if not added_to_inventory:
            results.append({"message": "Inventory is Full!"})
        else:
            results.append({"message": f"{item.name} added to inventory."})

        return results

    def remove_item(self, item):
        item_idx = self.items.index(item)
        self.items[item_idx] = None
