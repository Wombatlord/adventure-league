from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.item.effects import (
    apply_heal_consumption_effect,
    apply_heal_on_hit_effect,
)
from src.entities.item.inventory_item import Consumable, Exhaustable, Throwable

if TYPE_CHECKING:
    from src.entities.entity import Entity


class HealingPotion(Exhaustable, Consumable, Throwable):
    effect_name = "heal"
    name = "healing potion"
    consume_effect_name = effect_name
    hit_effect_name = effect_name
    apply_consume_effect = apply_heal_consumption_effect
    apply_on_hit_effect = apply_heal_on_hit_effect
    action_point_cost = 1

    @classmethod
    def from_dict(cls, owner):
        return cls(owner)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
        }

    def __init__(self, owner: Entity, heal_amount=5) -> None:
        self.owner = owner
        owner.item = self
        self.heal_amount = heal_amount
