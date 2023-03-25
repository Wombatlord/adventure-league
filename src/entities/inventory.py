from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self

if TYPE_CHECKING:
    from src.entities.entity import Entity

Action = dict[str, Any]


class Inventory:
    def __init__(self, owner: Entity, capacity: int = 0) -> None:
        self.owner = owner
        self._capacity = 0
        self.capacity = capacity
        self.items: list = [None for _ in range(self.capacity)]

    def get_capacity(self):
        return self._capacity

    def set_capacity(self, value):
        self._capacity = value
        while len(self.items) < self.capacity:
            self.items.append(None)

    def add_item_to_inventory(self, item: InventoryItem) -> list[Action]:
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
            item.on_add_to_inventory(self)
            results.append({"message": f"{item.name} added to inventory."})

        return results

    def __contains__(self, item: InventoryItem) -> bool:
        return item in self.items

    def remove_item(self, item):
        if item in self:
            item_idx = self.items.index(item)
            self.items[item_idx] = None


class InventoryItem:
    name = ""

    def get_name(self) -> str:
        return self.name or "no name"

    def on_add_to_inventory(self, inventory: Inventory):
        pass


Effect = Callable[[InventoryItem, Inventory], Action]


class Exhaustable(InventoryItem):
    on_exhausted_hooks: list[Callable[[], None]] | None = None

    def on_add_to_inventory(self, inventory: Inventory):
        if not self.on_exhausted_hooks:
            self.on_exhausted_hooks = [lambda: inventory.remove_item(self)]

    def exhaust(self):
        while self.on_exhausted_hooks and (hook := self.on_exhausted_hooks.pop()):
            hook()


class Consumable(InventoryItem):
    consume_effect_name = ""
    apply_consume_effect: Effect

    def get_consume_effect_name(self) -> str:
        return self.consume_effect_name or "no effect"

    def get_consume_effect(self) -> Callable[[Self, Inventory], Action]:
        return self.apply_consume_effect

    def consume(self, inventory: Inventory) -> Action:
        effect_data = {}
        if hasattr(self, "apply_consume_effect"):
            effect_data = self.get_consume_effect()(inventory)
        if issubclass(self.__class__, Exhaustable):
            self.exhaust()

        return inventory.owner.annotate_event(
            {
                "message": f"{self.get_name()} used by {inventory.owner.name}",
                "item_consumed": {
                    "consumable": self,
                    "effect": {
                        "name": self.get_consume_effect_name(),
                        "target": self.owner,
                        "details": effect_data,
                    },
                },
            }
        )


class Throwable(InventoryItem):
    hit_effect_name = ""
    apply_on_hit_effect: Effect

    def get_hit_effect_name(self) -> str:
        return self.hit_effect_name or "no hit effect"

    def get_on_hit_effect(self) -> Callable[[Self, Inventory], dict]:
        return self.apply_on_hit_effect

    def throw(self, inventory: Inventory, target: Entity) -> Action:
        effect_data = {}
        if hasattr(self, "apply_on_hit_effect"):
            effect_data = self.get_consume_effect()(target)

        return inventory.owner.annotate_event(
            {
                "message": f"{self.get_name()} used by {inventory.owner.name}",
                "thowable_hit": {
                    "throwable": self,
                    "effect": {
                        "name": self.get_hit_effect_name(),
                        "target": self.owner,
                        "details": effect_data,
                    },
                },
            }
        )
