from __future__ import annotations

import random
from typing import Callable, NamedTuple

from src.entities.combat.modifiable_stats import (Modifier, namedtuple_add,
                                                  namedtuple_sub)


class HealthPool:
    def __init__(self, max: int, current: int = None, bonus: int = 0) -> None:
        self._max_hp = max
        self._current_hp = current or max
        self._bonus_hp = bonus

    @property
    def max_hp(self):
        return self._max_hp

    @max_hp.setter
    def max_hp(self, value: int):
        self._max_hp = value

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

    def full_heal(self):
        self._current_hp = self.max_hp

    def set_shield(self, amount: int):
        self._bonus_hp = amount


class FighterStats(NamedTuple):
    name = "FighterStats"
    defence: int = 0
    power: int = 0
    speed: int = 0
    base_xp_value: int = 1000

    def __add__(self, other):
        return namedtuple_add(self.__class__, self, other)

    def __sub__(self, other):
        return namedtuple_sub(self.__class__, self, other)


class EquippableItemStats(NamedTuple):
    name = "EquippableStats"
    crit: float = 0
    block: float = 0
    evasion: float = 0
    attack_dice: int = 0
    attack_dice_faces: int = 0

    def __add__(self, other):
        return namedtuple_add(self.__class__, self, other)

    def __sub__(self, other):
        return namedtuple_sub(self.__class__, self, other)

    def display_stats(self, delim: str = " | ") -> str:
        dict_val = self._asdict()

        dmg_string = f"Attack: {self.attack_dice}d{self.attack_dice_faces}"
        dict_val.pop("attack_dice")
        dict_val.pop("attack_dice_faces")

        attributes = [dmg_string]

        for stat_name, value in dict_val.items():
            readable_name = stat_name.replace("_", " ").title()
            if isinstance(value, float):
                value = f"{value:.1f}"
            readable_stat = f"{readable_name}: {value}"
            attributes.append(readable_stat)

        return delim.join(attributes)


class StatAffix(NamedTuple):
    name: str
    modifier: Modifier[FighterStats | EquippableItemStats]


modifiers = {
    "bear": lambda: Modifier(
        FighterStats, base=FighterStats(power=random.randint(1, 3))
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
    "eagle": lambda: Modifier(
        EquippableItemStats, percent=EquippableItemStats(crit=random.randint(1, 5))
    ),
}


def affix_from_modifier(name: str) -> StatAffix:
    return StatAffix(
        name=name,
        modifier=modifiers.get(name, lambda: Modifier(FighterStats))(),
    )


# These are lambdas so that an Equippable can roll a fresh affix on instantiation.
raw_power_increase = lambda: affix_from_modifier("bear")
percent_power_increase = lambda: affix_from_modifier("tiger")
raw_defence_increase = lambda: affix_from_modifier("bull")
percent_defence_increase = lambda: affix_from_modifier("jaguar")
percent_crit_increase = lambda: affix_from_modifier("eagle")
