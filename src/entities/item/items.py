from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Self

import yaml

from src.entities.item.effects import (
    apply_heal_consumption_effect,
    apply_heal_on_hit_effect,
)
from src.entities.item.inventory import Consumable, Exhaustable, Throwable

if TYPE_CHECKING:
    from src.entities.entity import Entity


class HealingPotion(Exhaustable, Consumable, Throwable, yaml.YAMLObject):
    effect_name = "heal"
    name = "healing potion"
    consume_effect_name = effect_name
    hit_effect_name = effect_name
    apply_consume_effect = apply_heal_consumption_effect
    apply_on_hit_effect = apply_heal_on_hit_effect
    action_point_cost = 1
    yaml_tag = "!HealingPotion"

    @classmethod
    def to_yaml(cls, dumper: yaml.Dumper, item: Self) -> str:
        e = cls(item.owner)
        e.__dict__ = {**item.__dict__}

        e.__dict__.pop("on_exhausted_hooks")

        return dumper.represent_yaml_object(
            cls.yaml_tag,
            e,
            cls,
            flow_style=cls.yaml_flow_style,
        )

    @classmethod
    def from_yaml(cls, loader: yaml.Loader, node=None) -> Self:
        item_gen: Generator[HealingPotion, None, None] = loader.construct_yaml_object(
            node, cls
        )
        item = next(item_gen)
        try:
            next(item_gen)
        except StopIteration:
            pass

        item.on_add_to_inventory(item.owner.inventory)

        return item

    def __init__(self, owner: Entity, heal_amount=5) -> None:
        self.owner = owner
        owner.item = self
        self.heal_amount = heal_amount
