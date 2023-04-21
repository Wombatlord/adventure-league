from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, Optional

from src.entities.action.actions import ActionMeta, BaseAction
from src.entities.magic.spells import EffectType, Spell
from src.world.node import Node

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.magic.spells import Spell, SpellFactory

Event = dict[str, Any]


class MagicAction(BaseAction, metaclass=ActionMeta):
    name = "cast spell"

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

            match spell.effect_type:
                case EffectType.SELF:
                    yield spell.self_cast()
                case EffectType.ENTITY:
                    yield spell.entity_cast(fighter, target=target.owner)
                case EffectType.AOE:
                    template = spell.aoe_at_node(target)
                    yield spell.aoe_cast(targets=template.shape)

        else:
            yield {"message": f"Not enough mana to cast {spell.name}!"}

    @classmethod
    def details(cls, fighter: Fighter, target: Fighter) -> dict:
        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": lambda: fighter.ready_action(cls(fighter, target)),
            "subject": target,
            "label": f"{target.owner.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter, spell: Spell) -> list[dict]:
        return [
            cls.details(fighter, occupant.fighter)
            for occupant in fighter.locatable.entities_in_range(
                room=fighter.encounter_context.get(),
                max_range=spell.max_range,
                entity_filter=lambda e: fighter.is_enemy_of(e.fighter),
            )
        ]

    def __init__(self, fighter: Fighter, target: Fighter) -> None:
        self.fighter = fighter
        self.target = target

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.target)


class MpPool:
    def __init__(self, max):
        self._max = max
        self._current = max

    def spend(self, amount: int):
        self._current -= amount

    def can_cast(self, spell: Spell) -> bool:
        return self.can_spend(spell.cost)

    def can_spend(self, amount: int) -> bool:
        return self._current >= amount

    def recharge(self, amount: int | None = None):
        """
        Supply an amount to recharge by that amount (capped at max mp).
        Default behaviour is recharge to max.
        """
        if amount is None:
            self._current = self._max

        else:
            self._current = min(self._max, self._current + amount)

    @property
    def current(self) -> int:
        return self._current


class Caster:
    def __init__(self, max_mp: int, known_spells: list[SpellFactory]):
        self.owner: Optional[Fighter] = None
        self.mp_pool = MpPool(max=max_mp)
        self.spells = [spell(self) for spell in known_spells]

    def set_owner(self, owner: Caster) -> Caster:
        self.owner = owner
        return self

    def available_spells(self):
        return [
            {
                "label": spell.name,
                "mp_cost": spell.mp_cost,
                "self_target": spell.is_self_target(),
                "valid_target": spell.valid_target,
                "aoe_template": spell.aoe_at_node,
                "on_confirm": spell.cast,
            }
            for spell in self.spells
        ]

    @property
    def current_mp(self) -> int:
        return self.mp_pool.current

    def learn_spell(self, spell: SpellFactory) -> bool:
        if spell not in self.spells:
            self.spells.append(spell(self))
            return True
        else:
            return False


# event = {
#     "choices": {
#         "move": [],
#         "cast spell": {
#             [
#                 {
#                     "label": "magic missile",
#                     "mp_cost": 1,
#                     "valid_target": lambda target: False,
#                     "aoe_template": lambda anchor: "AoETemplate(anchor, (anchor,))",
#                     "on_confirm": "MagicMissile().cast()",
#                 }
#             ],
#         },
#     },
# }
