from typing import Any

from src.entities.entity import Entity
from src.entities.inventory import Consumable, Inventory, Throwable

Action = dict[str, Any]


def apply_heal_consumption_effect(self: Consumable, inventory: Inventory) -> Action:
    hp_before = inventory.owner.fighter.hp
    if inventory.owner.fighter.hp <= inventory.owner.fighter.max_hp:
        inventory.owner.fighter.hp = min(
            inventory.owner.fighter.max_hp,
            inventory.owner.fighter.hp + self.heal_amount,
        )

    return {"heal_amount": inventory.owner.fighter.hp - hp_before}


def apply_heal_on_hit_effect(self: Throwable, target: Entity) -> Action:
    hp_before = target.fighter.hp
    if target.fighter.hp < target.fighter.max_hp:
        target.fighter.hp = min(target.fighter.max_hp, target.fighter.hp - hp_before)

    return {"heal_amount": target.fighter.hp - self.heal_amount}
