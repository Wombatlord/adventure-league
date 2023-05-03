from __future__ import annotations

from typing import Callable, NamedTuple


class HealthPool:
    def __init__(self, max: int) -> None:
        self._max_hp = max
        self._current_hp = max
        self._bonus_hp = 0

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def current(self):
        return self._current_hp

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


class FighterStats:
    defence: int
    power: int
    level: int
    speed: int

    def __init__(self, defence, power, level, speed) -> None:
        self._defence = defence
        self._power = power
        self._level = level
        self._speed = speed
        self.modifiers: tuple[StatAffix, int] = []

    @property
    def defence(self):
        return self._defence

    @defence.setter
    def defence(self, value):
        self._defence = value

    @property
    def power(self):
        return self._power

    @property
    def level(self):
        return self._level

    @property
    def speed(self):
        return self._speed

    def sort_modifiers(self):
        def sorting(m):
            return m.application_order

        self.modifiers = sorted(self.modifiers, key=sorting)

    def calculate_modifiers(self) -> dict[str, int]:
        self.sort_modifiers()
        new_power = 0
        new_defence = 0
        for i, mod in enumerate(self.modifiers):
            match mod[i].target_stat:
                case "power":
                    new_power += mod[i].effect(mod[1])
                case "defence":
                    new_defence += mod[i].effect(mod[1])

        return {"new_power": new_power, "new_defence": new_defence}


class StatAffix(NamedTuple):
    name: str
    target_stat: str
    effect: Callable[[int], int]
    application_order: int


class Modifiers:
    @staticmethod
    def percent_increase(stat, mod) -> int:
        return stat + (mod // stat) * 100

    @staticmethod
    def raw_increase(stat, mod):
        return stat + mod


RawPowerIncrease = StatAffix(
    name="bear",
    target_stat="power",
    effect=Modifiers.raw_increase,
    application_order=0,
)
PercentPowerIncrease = StatAffix(
    name="tiger",
    target_stat="power",
    effect=Modifiers.percent_increase,
    application_order=1,
)
RawDefenceIncrease = StatAffix(
    name="bull",
    target_stat="defence",
    effect=Modifiers.raw_increase,
    application_order=0,
)
PercentDefenceIncrease = StatAffix(
    name="jaguar",
    target_stat="defence",
    effect=Modifiers.percent_increase,
    application_order=1,
)
