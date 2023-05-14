from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from src.entities.action.actions import ActionMeta, BaseAction
from src.entities.magic.spells import EffectType, Spell
from src.world.node import Node

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.magic.spells import Spell

Event = dict[str, Any]


class MagicAction(BaseAction, metaclass=ActionMeta):
    name = "cast spell"
    menu_pos = 1

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(
        cls, fighter: Fighter, target: Fighter | Node, spell: Spell
    ) -> Generator[Event]:
        if fighter.caster.mp_pool.can_cast(spell) and fighter.caster.mp_pool.can_spend(
            spell.mp_cost
        ):
            fighter.action_points.deduct_cost(cls.cost(fighter))
            fighter.caster.mp_pool.spend(spell.mp_cost)

            yield from spell.cast(target)

        else:
            yield {"message": f"Not enough mana to cast {spell.name}!"}

    @classmethod
    def details(cls, fighter: Fighter, spell: Spell) -> dict:
        if spell.effect_type == EffectType.SELF:
            # for a self cast, we know the target is the caster
            on_confirm = lambda: fighter.ready_action(cls(fighter, fighter, spell))
        else:
            # otherwise we need targeting input
            on_confirm = lambda target: fighter.ready_action(
                cls(fighter, target, spell)
            )

        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": on_confirm,
            "subject": spell,
            "label": f"{spell.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [
            cls.details(fighter, spell)
            for spell in fighter.gear.weapon.available_spells
        ]

    def __init__(self, fighter: Fighter, target: Fighter, spell: Spell) -> None:
        self.fighter = fighter
        self.target = target
        self.spell = spell

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.target, self.spell)
