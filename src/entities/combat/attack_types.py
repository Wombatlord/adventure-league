from __future__ import annotations

import abc
import math
import random
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Self

from src.world.node import Node

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity

Event = dict[str, Any]


class RollOutcome(Enum):
    PERFECT_SUCCESS = 2
    SUCCESS = 1
    FAIL = 0
    CRITICAL_FAIL = -1

    def __and__(self, other):
        return self.value >= 1 and other

    def __or__(self, other):
        return self.value >= 1 or other

    @classmethod
    def from_percent(cls, chance: PercentChance) -> Self:
        match chance.as_percent(), chance.outcome():
            case x, False if x < 5:
                return cls.CRITICAL_FAIL
            case x, True if x >= 95:
                return cls.PERFECT_SUCCESS
            case _, False:
                return cls.FAIL
            case _:
                return cls.SUCCESS


class PercentChance:
    _value: int
    _roll: int | None

    def __init__(self, value: int) -> None:
        self._value = max(min(int(value), 99), 1)
        self._roll = None

    def as_probability(self) -> float:
        return (self._value + 1) / 100

    def as_percent(self) -> int:
        return self._value

    def outcome(self) -> bool:
        if self._roll is None:
            self._roll = random.randint(0, 99)
        return self._roll < self._value

    def get_roll(self) -> int:
        return self._roll

    def __str__(self) -> str:
        return f"{self._value}%"


def make_probability_func(
    sensitivity: float | int, accuracy: int = 0
) -> Callable[[float | int], float]:
    return lambda delta: 1 / 2 + math.atan((delta + accuracy) / sensitivity) / math.pi


class AttackRules:
    @staticmethod
    def chance_to_hit(attacker: Fighter, target: Entity) -> PercentChance:
        p = attacker.stats.power
        d = target.fighter.stats.defence

        to_hit = make_probability_func(sensitivity=5)

        return PercentChance(100 * to_hit(p - d))

    @staticmethod
    def damage_amount(attacker: Fighter, target: Entity) -> int:
        actual_damage = int(
            2
            * attacker.stats.power**2
            / (attacker.stats.power + target.fighter.stats.defence)
        )

        if target.fighter.health.current - actual_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            attacker.in_combat = False

        return actual_damage


def attack_details(fighter: Fighter, target: Entity) -> Event:
    result = {}
    if fighter.owner.is_dead:
        raise ValueError(f"{fighter.owner.name=}: I'm dead jim.")

    if target.is_dead:
        raise ValueError(f"{target.name=}: He's dead jim.")

    # For choosing attack animation sprites
    fighter.in_combat = True
    target.fighter.in_combat = True

    match RollOutcome.from_percent(AttackRules.chance_to_hit(fighter, target)):
        case RollOutcome.CRITICAL_FAIL:
            message = f"{fighter.owner.name} fails to hit {target.name} embarrasingly!"
            fighter.commence_retreat()
        case RollOutcome.FAIL:
            message = f"{fighter.owner.name} fails to hit {target.name}!"
        case _:
            actual_damage = AttackRules.damage_amount(fighter, target)
            message = f"{fighter.owner.name} hits {target.name} for {actual_damage}\n"
            damage_details = target.fighter.take_damage(actual_damage)

            result.update(**damage_details)

    result.update({"attack": fighter.owner, "message": message})
    return result


class WeaponAttack(metaclass=abc.ABCMeta):
    ap_cost: int = 0
    name: str = ""
    max_range: int = 0
    _fighter: Fighter
    weapon_type: str = ""

    @abc.abstractmethod
    def attack(self, target) -> Event:
        raise NotImplementedError()

    @abc.abstractmethod
    def valid_target(self, target: Fighter | Node) -> bool:
        raise NotImplementedError()

    @property
    def fighter(self):
        return self._fighter


class NormalAttack(WeaponAttack):
    name: str = "Normal Attack"
    ap_cost: int = 1
    max_range: int = 1

    def __init__(self, fighter) -> None:
        self._fighter = fighter

    def attack(self, target: Entity) -> Event:
        result = {}
        if self._fighter.owner.is_dead:
            raise ValueError(f"{self._fighter.owner.name=}: I'm dead jim.")

        if target.is_dead:
            raise ValueError(f"{target.name=}: He's dead jim.")

        # For choosing attack animation sprites
        self._fighter.in_combat = True
        target.fighter.in_combat = True

        match RollOutcome.from_percent(
            AttackRules.chance_to_hit(self._fighter, target)
        ):
            case RollOutcome.CRITICAL_FAIL:
                message = f"{self._fighter.owner.name} fails to hit {target.name} embarrasingly!"
                self._fighter.commence_retreat()
            case RollOutcome.FAIL:
                message = f"{self._fighter.owner.name} fails to hit {target.name}!"
            case _:
                actual_damage = AttackRules.damage_amount(self._fighter, target)
                message = f"{self._fighter.owner.name} hits {target.name} for {actual_damage}\n"
                damage_details = target.fighter.take_damage(actual_damage)

                result.update(**damage_details)

        result.update({"attack": self._fighter.owner, "message": message})
        return result

    def valid_target(self, target: Fighter | Node) -> bool:
        if not hasattr(target, "location"):
            return False

        if target.location is None:
            return False

        range = self._fighter.locatable.entities_in_range(
            room=self._fighter.encounter_context.get(),
            max_range=self._fighter.stats.max_range,
            entity_filter=lambda e: self._fighter.is_enemy_of(e.fighter),
        )

        can_see = target.owner in range and self._fighter.can_see(target)
        return can_see

    def aoe_at_node(self, node: Node | None = None) -> tuple[Node, ...] | None:
        if node is None:
            return tuple()
        if not isinstance(node, Node):
            raise TypeError(f"Expected a Node, got {node=}")

        return (node,)


attack_types = [NormalAttack]
