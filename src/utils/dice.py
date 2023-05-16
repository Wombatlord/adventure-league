from __future__ import annotations

import random
from typing import Callable, Self


class D:
    _roll: Callable[[], int]

    def __init__(self, faces: int):
        if faces:
            self._roll = lambda: random.randint(1, faces)
        else:
            self._roll = lambda: 0

    def __call__(self) -> int:
        return self._roll()

    def roll(self) -> int:
        return self()

    @classmethod
    def from_roll(cls, roll: Callable) -> Self:
        d = object.__new__(cls)
        d._roll = roll
        return d

    @classmethod
    def from_die_vec(cls, vec: list[tuple[int, int]]) -> Self:
        d = D(0)
        for count, faces in vec:
            d += count * D(faces)

        return d

    def __rmul__(self, other: int | Self) -> Self:
        if isinstance(other, int):
            return D.from_roll(lambda: sum([self() for _ in range(other)]))

        return D.from_roll(lambda: other() * self())

    def __mul__(self, other: int | Self):
        return self.__rmul__(other)

    def __add__(self, other: int | float | Self) -> Self:
        if isinstance(other, int | float):
            return D.from_roll(lambda: other + self())

        return D.from_roll(lambda: other() + self())

    def __sub__(self, other):
        if isinstance(other, int | float):
            return D.from_roll(lambda: self() - other)

        return D.from_roll(lambda: self() - other())

    def __rsub__(self, other):
        if isinstance(other, int | float):
            return D.from_roll(lambda: other - self)

        return D.from_roll(lambda: other - self())

    def __radd__(self, other: int | float | Self) -> Self:
        return self.__add__(other)

    def __iadd__(self, other: int | float | Self):
        return self.__add__(other)
