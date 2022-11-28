from typing import NamedTuple

class Cycle:
    def __init__(self, length: int, pos: int = 0) -> None:
        self.length = length
        self.pos = pos

    def incr(self):
        if self.length == 0:
            return
        self.pos = (self.pos + 1) % self.length

    def decr(self):
        if self.length == 0:
            return
        self.pos = (self.pos - 1) % self.length


class Coords(NamedTuple):
    x: int
    y: int

class Grid:
    axes: tuple[Cycle, Cycle]
    def __init__(
        self, 
        size: tuple[int, int], # (width, height) 
        pos: tuple[int,int] = (0,0), # (x, y)
    ) -> None:
        self.axes = tuple(
            Cycle(length, start) for length, start in zip(size, pos)
        )

    def current(self) -> Coords:
        return Coords(self.axes[0].pos, self.axes[1].pos)

    def left(self):
        self.axes[0].decr()

    def right(self):
        self.axes[0].incr()

    def up(self):
        self.axes[1].incr()

    def down(self):
        self.axes[1].decr()