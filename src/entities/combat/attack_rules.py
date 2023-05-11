from __future__ import annotations

import math
import random
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Self

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
                print(x)
                return cls.FAIL
            case _:
                print(x)
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
        p = attacker.modifiable_stats.current.power
        d = target.fighter.modifiable_stats.current.defence

        to_hit = make_probability_func(sensitivity=5)

        return PercentChance(100 * to_hit(p - d))

    @staticmethod
    def damage_amount(attacker: Fighter, target: Entity) -> int:
        p = attacker.modifiable_stats.current.power
        d = target.fighter.modifiable_stats.current.defence
        actual_damage = 2 * int(p**2 / (p + d))

        if target.fighter.health.current - actual_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            attacker.in_combat = False

        return actual_damage
