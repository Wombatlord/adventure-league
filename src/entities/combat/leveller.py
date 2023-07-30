from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Self

if TYPE_CHECKING:
    from src.engine.engine import Event
    from src.entities.combat.fighter import Fighter


class Leveller:
    owner: Fighter
    xp_to_resolve: list[Experience]

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
        return (self.current_level + 1) * 1000

    @property
    def current_xp(self) -> int:
        return self._current_xp

    def should_level_up(self) -> Generator[Event, None, None]:
        return self.current_xp >= self.xp_to_level_up

    def _do_level_up(self):
        self._current_xp = 0
        self._current_level += 1

        new_power = self.owner.stats.power + 1
        new_def = self.owner.stats.defence + 1
        self.owner.stats._replace(power=new_power)
        self.owner.stats._replace(defence=new_def)
        self.owner.health.max_hp += 10
        self.owner.health.full_heal()

        if self.owner.caster:
            self.owner.caster.mp_pool.max += 5
            self.owner.caster.mp_pool.recharge()

    def gain_xp(self, amount: Experience) -> Generator[Event, None, None]:
        self._current_xp += amount.xp_value

        if self.should_level_up():
            self._do_level_up()


class Experience:
    def __init__(self, xp_value: int = 50) -> None:
        self.xp_value = xp_value

    def __add__(self, xp: Self) -> Self:
        final_xp = self.xp_value + xp.xp_value
        return Experience(xp_value=final_xp)

    def __floordiv__(self, other) -> Self:
        if isinstance(other, int):
            return Experience(self.xp_value // other)
        elif isinstance(other, Experience):
            return Experience(self.xp_value // other.xp_value)

    def resolve_xp(self, leveller: Leveller):
        leveller.gain_xp(self.xp_value)
