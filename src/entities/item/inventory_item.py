from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self

from src.engine.events_enum import Events

if TYPE_CHECKING:
    from src.entities.entity import Entity
    from src.entities.item.inventory import Inventory


class InventoryItem:
    name = ""

    def get_name(self) -> str:
        return self.name or "no name"

    def on_add_to_inventory(self, inventory: Inventory):
        pass


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

    def get_consume_effect(self) -> Callable[[Self, Inventory], Event]:
        return self.apply_consume_effect

    def consume(self, inventory: Inventory) -> Event:
        effect_data = {}
        item_consumed = None

        if hasattr(self, "apply_consume_effect"):
            effect_data = self.get_consume_effect()(inventory)
            item_consumed = {
                "consumable": self,
                "effect": {
                    "name": self.get_consume_effect_name(),
                    "target": self.owner,
                    "details": effect_data,
                },
            }
        if issubclass(self.__class__, Exhaustable):
            self.exhaust()

        event = {
            "item_consumed": item_consumed,
        }
        if item_consumed:
            event = inventory.owner.annotate_event(
                {
                    **event,
                    Events.MESSAGE: f"{self.get_name()} used by {inventory.owner.name}",
                }
            )

        return event


class Throwable(InventoryItem):
    hit_effect_name = ""
    apply_on_hit_effect: Effect

    def get_hit_effect_name(self) -> str:
        return self.hit_effect_name or "no hit effect"

    def get_on_hit_effect(self) -> Callable[[Self, Inventory], dict]:
        return self.apply_on_hit_effect

    def throw(self, inventory: Inventory, target: Entity) -> Event:
        effect_data = {}
        if hasattr(self, "apply_on_hit_effect"):
            effect_data = self.get_consume_effect()(target)

        return inventory.owner.annotate_event(
            {
                Events.MESSAGE: f"{self.get_name()} used by {inventory.owner.name}",
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


if TYPE_CHECKING:
    Event = dict[str, Any]
    Effect = Callable[[InventoryItem, Inventory], Event]
