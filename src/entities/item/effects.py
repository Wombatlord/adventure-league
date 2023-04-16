from typing import Any

from src.entities.entity import Entity
from src.entities.item.inventory import Consumable, Inventory, Throwable

Event = dict[str, Any]


def apply_heal_consumption_effect(self: Consumable, inventory: Inventory) -> Event:
    hp_before = inventory.owner.fighter.hp
    if inventory.owner.fighter.hp <= inventory.owner.fighter.max_hp:
        inventory.owner.fighter.hp = min(
            inventory.owner.fighter.max_hp,
            inventory.owner.fighter.hp + self.heal_amount,
        )

    return {"heal_amount": inventory.owner.fighter.hp - hp_before}


def apply_heal_on_hit_effect(self: Throwable, target: Entity) -> Event:
    hp_before = target.fighter.hp
    if target.fighter.hp < target.fighter.max_hp:
        target.fighter.hp = min(target.fighter.max_hp, target.fighter.hp - hp_before)

    return {"heal_amount": target.fighter.hp - self.heal_amount}
