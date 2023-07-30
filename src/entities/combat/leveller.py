from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Self

from src.utils import deep_copy

if TYPE_CHECKING:
    from src.engine.engine import Event
    from src.entities.combat.fighter import Fighter


class Leveller:
    owner: Fighter
    xp_to_resolve: list[Experience]

    @staticmethod
    def delta_xp(from_level) -> int:
        if from_level < 0:
            return 0
        return (from_level + 1) * 1000

    def __init__(self, owner) -> None:
        self.owner = owner
        self._current_level = 0
        self._current_xp = 0
        self._xp_to_level_up = 1000
        self.xp_to_resolve = []

    @property
    def current_level(self) -> int:
        return self._current_level

    @property
    def xp_to_level_up(self):
        return self.delta_xp(self.current_level)

    @property
    def total_xp(self) -> int:
        lvl = self.current_level
        xp_acc = self.current_xp
        while (lvl := lvl - 1) > -1:
            xp_acc += self.delta_xp(lvl)

        return xp_acc

    @property
    def current_xp(self) -> int:
        return self._current_xp

    def should_level_up(self) -> bool:
        return self.current_xp >= self.xp_to_level_up

    def _do_level_up(self):
        self._current_xp = 0
        self._current_level += 1
        if not self.owner:
            return
        new_power = self.owner.stats.power + 1
        new_def = self.owner.stats.defence + 1
        self.owner.stats._replace(power=new_power)
        self.owner.stats._replace(defence=new_def)
        self.owner.health.max_hp += 10
        self.owner.health.full_heal()

        if self.owner.caster:
            self.owner.caster.mp_pool.max += 5
            self.owner.caster.mp_pool.recharge()

    def gain_xp(self, amount: Experience | int) -> Generator[Event, None, None]:
        xp_change = amount
        if isinstance(xp_change, Experience):
            xp_change = xp_change.xp_value

        self._current_xp += xp_change

        if self.should_level_up():
            self._do_level_up()

    def disown_clone(self) -> Leveller:
        instance = Leveller(None)
        # should not modify the fighter if we want to use xp/levelling logic
        instance.__dict__ = {**deep_copy.copy(self.__dict__), "owner": None}

        return instance


class Experience:
    xp_value: int

    def __init__(self, xp_value: int = 50) -> None:
        self.xp_value = xp_value

    def __add__(self, xp: Self | int) -> Self:
        xp_change = xp if isinstance(xp, int) else xp.xp_value
        final_xp = self.xp_value + xp_change
        return Experience(xp_value=final_xp)

    def __floordiv__(self, other) -> Self:
        if isinstance(other, int):
            return Experience(self.xp_value // other)
        elif isinstance(other, Experience):
            return Experience(self.xp_value // other.xp_value)

    def resolve_xp(self, leveller: Leveller):
        leveller.gain_xp(self.xp_value)
