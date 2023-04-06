import json
from typing import Any, NamedTuple, Sequence


class Cycle:
    def __init__(self, length: int, pos: int = 0) -> None:
        self.length = length
        self.pos = pos

    def __str__(self) -> str:
        return json.dumps(self.__dict__)

    def __index__(self) -> int:
        return self.pos

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

    @property
    def max(self) -> int:
        return self.length - 1


# Generate a sequence of values for vertical alignments. Descending by default.
def gen_heights(
    desc: bool = True,
    row_height: int = 0,
    y: int = 0,
    spacing: int = 0,
    max_height: int | None = None,
) -> Sequence[int]:
    start = y - row_height * spacing
    incr = abs(row_height)  # Negative indicates down
    if desc:
        incr = -abs(incr)

    current = start
    while True:
        if max_height is not None and abs(start - current) >= max_height:
            break
        yield current

        # increment on subsequent calls
        current = current + incr


class ScrollWindow:
    _items: list
    visible_size: int
    stretch_limit: int
    position: Cycle
    _frame_offset: Cycle

    def __init__(
        self, items: list, visible_size: int, stretch_limit: int | None = None
    ) -> None:
        if stretch_limit is None:
            stretch_limit = visible_size

        self.stretch_limit = stretch_limit
        if visible_size > len(items):
            visible_size = len(items)
        if visible_size < 1:
            visible_size = 1
        self._frame_offset = Cycle(len(items) - visible_size + 1, pos=0)
        self.position = Cycle(len(items), pos=0)
        self.visible_size = visible_size
        self._items = [*items]

    def __str__(self) -> str:
        state = {**self.__dict__}

        for k, v in state.items():
            if isinstance(v, Cycle):
                state[k] = v.__dict__

        return json.dumps(state)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, new_items: list):
        if len(self._items) != len(new_items):
            self.position.length = len(new_items)

        self._items = new_items

    @property
    def frame_start(self) -> int:
        return self._frame_offset.pos

    @property
    def frame_end(self) -> int:
        return self._frame_offset.pos + self.visible_size

    @property
    def visible_items(self) -> tuple[list, int | None]:
        relative_position = self.position.pos - self._frame_offset.pos
        frame = self.items[self.frame_start : self.frame_end]
        return frame, relative_position if frame else None

    @property
    def selection(self) -> Any:
        if not self.items:
            return None
        return self.items[self.position.pos]

    def _drag_frame(self):
        drag = 0
        if self.position.pos >= self.frame_end:
            drag = self.position.pos - (self.frame_end - 1)

        elif self.position.pos < self.frame_start:
            drag = self.position.pos - self.frame_start

        self._frame_offset.incr(by=drag)

    def incr_selection(self):
        self.position.incr()
        self._drag_frame()

    def decr_selection(self):
        self.position.decr()
        self._drag_frame()

    def init_items(self, items):
        self.__init__(
            [*items],
            visible_size=self.visible_size,  # grow the frame size by 1 unless at max
            stretch_limit=self.stretch_limit,  # preserve stretch limit
        )

    def append(self, item):
        self.__init__(
            [*self.items, item],
            min(
                self.visible_size + 1, self.stretch_limit
            ),  # grow the frame size by 1 unless at max
            stretch_limit=self.stretch_limit,  # preserve stretch limit
        )

        # show the latest addition
        self.position.pos = len(self.items) - 1
        self._drag_frame()

    def append_all(self, items: list):
        for item in items:
            self.append(item)

    def pop(self, index: int = -1):
        """
        Behaves like array.pop but can be called with no arguments to pop the current selection
        """
        if index == -1:
            index = self.position.pos
        old_items = self.items
        old_position = self.position
        item = old_items.pop(index)

        self.__init__(old_items, self.visible_size, self.stretch_limit)
        self.position.pos = min(old_position.pos, self.position.max)
        self._drag_frame()
        return item


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
