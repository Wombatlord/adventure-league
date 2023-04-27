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

            yield from spell.cast(target)

        else:
            yield {"message": f"Not enough mana to cast {spell.name}!"}

    @classmethod
    def details(cls, fighter: Fighter, spell: Spell) -> dict:
        if spell.effect_type == EffectType.SELF:
            # for a self cast, we know the target is the caster
            on_confirm = lambda: fighter.ready_action(
                cls(fighter, fighter, spell)
            )
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
            cls.details(fighter, spell) for spell in fighter.caster.available_spells()
        ]

    def __init__(self, fighter: Fighter, target: Fighter, spell: Spell) -> None:
        self.fighter = fighter
        self.target = target
        self.spell = spell

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.target, self.spell)


class MpPool:
    def __init__(self, max):
        self._max = max
        self._current = max

    def spend(self, amount: int):
        self._current -= amount

    def can_cast(self, spell: Spell) -> bool:
        return self.can_spend(spell.mp_cost)

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
        return self.spells

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
