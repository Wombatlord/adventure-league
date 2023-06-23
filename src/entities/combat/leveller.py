from typing import Self


class Leveller:
    def __init__(self, owner) -> None:
        self.owner = owner
        self._current_level = 0
        self._current_xp = 0
        self._xp_to_level_up = 1000
        self.xp_to_resolve: list[Experience] | list[None] = []

    @property
    def current_level(self) -> int:
        return self._current_level

    @property
    def current_exp(self) -> int:
        return self._current_xp

    def increase_level(self):
        if self.current_exp >= self._xp_to_level_up:
            self._current_xp = 0
        self._current_level += 1

    def gain_exp(self, amount: int):
        self._current_xp += amount


class Experience:
    def __init__(self, xp_value: int = 50) -> None:
        self.xp_value = xp_value

    def __add__(self, xp: Self) -> Self:
        final_xp = self.xp_value + xp.xp_value
        return Experience(xp_value=final_xp)

    def resolve_xp(self, leveller: Leveller):
        leveller.gain_exp(self.xp_value)
