from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.entities.entity import Entity
    from src.entities.item.inventory import Consumable, Inventory, Throwable

Event = dict[str, Any]


def apply_heal_consumption_effect(self: Consumable, inventory: Inventory) -> Event:
    hp_before = inventory.owner.fighter.health.current
    if inventory.owner.fighter.health.current <= inventory.owner.fighter.health.max_hp:
        inventory.owner.fighter.health.current = min(
            inventory.owner.fighter.health.max_hp,
            inventory.owner.fighter.health.current + self.heal_amount,
        )

    return {"heal_amount": inventory.owner.fighter.health.current - hp_before}


def apply_heal_on_hit_effect(self: Throwable, target: Entity) -> Event:
    hp_before = target.fighter.health.current
    if target.fighter.health.current < target.fighter.health.max_hp:
        target.fighter.health.current = min(
            target.fighter.health.max_hp, target.fighter.health.current - hp_before
        )

    return {"heal_amount": target.fighter.health.current - self.heal_amount}
