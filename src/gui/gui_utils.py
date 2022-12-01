from typing import NamedTuple, Sequence, TypeVar

class Cycle:
    def __init__(self, length: int, pos: int = 0) -> None:
        self.length = length
        self.pos = pos

    def reset_pos(self, new_pos: int = 0):
        self.pos = new_pos

    # If the amount of things that can be cycled through changes,
    # ie. items are added or removed from a cyclable array,
    # use these to adjust the lengths of the cycle to ensure cycle length
    # and array length retain correspondence.
    def increase_length(self):
        self.length += 1

    def decrease_length(self):
        self.length -= 1

    # Cycle self.pos through the range of self.length.
    # First check length is not zero.
    # It may be zero if the collection the cycle is tracking has had all elements removed.
    # eg. all entities moved from a Roster to a Team or vice versa.
    def incr(self, by: int = 1):
        if self.length == 0:
            return
        self.pos = (self.pos + by) % self.length

    def decr(self, by: int = 1):
        if self.length == 0:
            return
        self.pos = (self.pos - by) % self.length

# Generate a sequence of values for vertical alignments. Descending by default.
def gen_heights(
    desc: bool = True, row_height: int = 0, height: int = 0, spacing: int = 0
) -> Sequence[int]:

    start = height - row_height * spacing
    incr = abs(row_height)  # Negative indicates down
    if desc:
        incr = -abs(incr)

    current = start
    while True:
        yield current

        # increment on subsequent calls
        current = current + incr


## BELOW BE EXPERIMENTS. ##
class Coords(NamedTuple):
    x: int
    y: int


class Grid:
    axes: tuple[Cycle, Cycle]

    def __init__(
        self,
        size: tuple[int, int],  # (width, height)
        pos: tuple[int, int] = (0, 0),  # (x, y)
    ) -> None:
        self.axes = tuple(Cycle(length, start) for length, start in zip(size, pos))

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

class ScrollWindow:
    items: list
    visible_size: int
    position: Cycle
    _frame_offset: Cycle

    def __init__(self, items: list, visible_size: int) -> None:
        if visible_size > len(items):
            visible_size = len(items)
        if visible_size < 1:
            visible_size = 1
        self._frame_offset = Cycle(len(items) - visible_size + 1, pos=0)
        self.position = Cycle(len(items), pos=0)
        self.visible_size = visible_size
        self.items = items

    @property
    def frame_start(self) -> int:
        return self._frame_offset.pos

    @property
    def frame_end(self) -> int:
        return self._frame_offset.pos + self.visible_size

    @property
    def visible_items(self) -> tuple[list, int | None]:
        relative_position = self.position.pos - self._frame_offset.pos
        frame = self.items[self.frame_start:self.frame_end]
        return frame, relative_position if frame else None

    def _drag_frame(self):
        drag = 0
        if self.position.pos >= self.frame_end:
            drag = self.position.pos - self.frame_end + 1
            
        elif self.position.pos < self.frame_start:
            drag = self.position.pos - self.frame_start

        self._frame_offset.incr(by=drag)

    def incr_selection(self):
        self.position.incr()
        self._drag_frame()
        
    def decr_selection(self):
        self.position.decr()
        self._drag_frame()

    def append(self, item):
        self.__init__([*self.items, item], self.visible_size)
        
        # show the latest addition
        self.position.pos = len(self.items) - 1
        self._drag_frame()
        