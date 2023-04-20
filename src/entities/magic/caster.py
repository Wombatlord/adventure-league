from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple, Optional

from src.entities.action.actions import ActionMeta, BaseAction
from src.world.node import Node

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class MagicAction(BaseAction, metaclass=ActionMeta):
    name = "cast spell"

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(
        cls, fighter: Fighter, target: Fighter, spell: Spell
    ) -> Generator[Event]:
        if fighter.caster.mp_pool.can_cast(spell) and fighter.caster.mp_pool.can_spend(
            spell.mp_cost
        ):
            fighter.action_points.deduct_cost(cls.cost(fighter))
            fighter.caster.mp_pool.spend(spell.mp_cost)
            yield spell.cast(fighter, target=target.owner)

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


Event = dict[str, Any]


class AoETemplate(NamedTuple):
    anchor: Node
    shape: tuple[Node]


class Spell(metaclass=abc.ABCMeta):
    # MAGIC MISSLE
    # FIREBALL
    # BUFF
    mp_cost: int = 0
    name: str = ""
    max_range: int = 0
    _caster: Caster

    def __init__(self, caster: Caster):
        self._caster = caster
        self._target = None

    # This seems a duplicate of MagicAction as the point of interaction with the downstream.
    @abc.abstractmethod
    def get_details(self) -> dict:
        raise NotImplementedError()

    @abc.abstractmethod
    def cast(self) -> Event:
        raise NotImplementedError()

    @abc.abstractmethod
    def valid_target(self, target: Node | Fighter) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def aoe_at_node(self, node: Node) -> AoETemplate | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def is_self_target(self) -> bool:
        raise NotImplementedError()


class MagicMissle(Spell):
    name: str
    mp_cost: int
    base_damage: int
    max_range: int

    def __init__(self, caster: Caster, name, mp_cost, base_damage, max_range):
        super().__init__(caster=caster)
        self.caster = caster
        self.name = name
        self.mp_cost = mp_cost
        self.base_damage = base_damage
        self.max_range = max_range

    # Is this the intention for this method rather than as in MagicAction?
    def get_details(self, target) -> dict:
        return {
            "on_confirm": lambda: self.cast(target),
            "subject": target,
            "label": self.name,
        }

    def cast(self, target) -> Event:
        return {"message": "cast magic missile"}

    def valid_target(self, target: Fighter) -> bool:
        if target.is_enemy_of(self.caster.owner):
            return True
        else:
            return False

    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return None

    def is_self_target(self) -> bool:
        return False


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


# This is what I understood to be the implication of "Factory"
SpellFactory = Callable[[Caster], Spell]
class SpellStatBlock(NamedTuple):
    spell: Spell
    name: str
    mp_cost: int
    damage: int
    max_range: int

    @property
    def factory(self) -> SpellFactory:
        return get_spell_factory(self)

    def spell_conf(self) -> dict:
        return {
            "name": self.name,
            "mp_cost": self.mp_cost,
            "damage": self.damage,
            "max_range": self.max_range,
        }


def get_spell_factory(stats: SpellStatBlock) -> SpellFactory:
    def _from_conf(spell_conf: dict) -> Spell:
        spell = stats.spell
        return spell(**spell_conf)

    def factory(caster):
        conf = stats.spell_conf()
        spell = _from_conf(conf)
        spell.caster = caster

        return spell

    return factory


_magic_missile = SpellStatBlock(
    spell=MagicMissle,
    name="magic missile",
    mp_cost=1,
    damage=5,
)
create_magic_missile = _magic_missile.factory

# example
basic_spell_book = [create_magic_missile]

event = {
    "choices": {
        "move": [],
        "cast spell": {
            [
                {
                    "label": "magic missile",
                    "mp_cost": 1,
                    "valid_target": lambda target: False,
                    "aoe_template": lambda anchor: AoETemplate(anchor, (anchor,)),
                    "on_confirm": MagicMissle().cast(),
                }
            ],
        },
    },
}
