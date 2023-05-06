from __future__ import annotations

import random
from typing import NamedTuple

from src.entities.combat.modifiable_stats import Modifier, namedtuple_add


class HealthPool:
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def to_dict(self):
        return {"max": self.max_hp, "current": self.current, "bonus": self.bonus}

    def __init__(self, max: int, current: int = None, bonus:int = 0) -> None:
        self._max_hp = max
        self._current_hp = current or max
        self._bonus_hp = bonus

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def current(self):
        return self._current_hp

    @property
    def bonus(self):
        return self._bonus_hp

    @bonus.setter
    def bonus(self, value):
        self._bonus_hp = value

    @current.setter
    def current(self, value):
        self._current_hp = value

    def _decrease_bonus_hp(self, amount) -> int:
        if self._bonus_hp - amount < 0:
            breakthrough = self._bonus_hp - amount
            self._bonus_hp = 0
            return abs(breakthrough)

        else:
            self._bonus_hp -= amount
            return 0

    def decrease_current(self, amount: int):
        if self._bonus_hp > 0:
            breakthrough = self._decrease_bonus_hp(amount)
            self._current_hp -= breakthrough

        elif self._current_hp - amount < 0:
            self._current_hp = 0

        else:
            self._current_hp -= amount

    def increase_current(self, amount: int):
        self._current_hp = min(self._current_hp + amount, self._max_hp)

    def set_shield(self, amount: int):
        self._bonus_hp = amount


class FighterStats(NamedTuple):
    name = "FighterStats"
    defence: int = 0
    power: int = 0
    level: int = 0
    speed: int = 0

    def __add__(self, other):
        return namedtuple_add(self.__class__, self, other)


class EquippableStats(NamedTuple):
    attack: int = 0
    block: int = 0
    evasion: int = 0


class StatAffix(NamedTuple):
    name: str
    modifier: Modifier[FighterStats]

    def to_dict(self):
        return {
            "name": self.name,
            "modifier": self.modifier.to_dict()
        }
    
modifiers = {
    "bear": lambda: Modifier(
        FighterStats, base=FighterStats(power=random.randint(1, 13))
    ),
    "tiger": lambda: Modifier(
        FighterStats, percent=FighterStats(power=random.randint(20, 60))
    ),
    "bull": lambda: Modifier(
        FighterStats, base=FighterStats(defence=random.randint(1, 3))
    ),
    "jaguar": lambda: Modifier(
        FighterStats, percent=FighterStats(defence=random.randint(20, 60))
    ),
}


def affix_from_modifier(name: str) -> StatAffix:
    return StatAffix(
        name=name,
        modifier=modifiers.get(name, lambda: Modifier(FighterStats))(),
    )


RawPowerIncrease = affix_from_modifier("bear")
PercentPowerIncrease = affix_from_modifier("tiger")
RawDefenceIncrease = affix_from_modifier("bull")
PercentDefenceIncrease = affix_from_modifier("jaguar")
