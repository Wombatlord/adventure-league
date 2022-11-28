from typing import NamedTuple

class Cycle:
    def __init__(self, length: int, pos: int = 0) -> None:
        self.length = length
        self.pos = pos

    def reset_pos(self, new_pos: int = 0):
        self.pos = new_pos

    # If the amount of things that can be cycled through changes,
    # use these to adjust the lengths of the cycle to ensure pos never
    # corresponds to an "empty" slot in the cycle
    def increase_length(self):
        self.length += 1
    
    def decrease_length(self):
        self.length -= 1

    # Cycle self.pos through the range of self.length.
    # First check length is not zero.
    # It may be zero if the collection the cycle is tracking has had all elements removed.
    # eg. all entities moved from a Roster to a Team or vice versa.
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