import operator
from typing import Callable, Generic, Self, Sequence, TypeVar

_SelectionType = TypeVar("_SelectionType", bound=object)


class Selection(Generic[_SelectionType]):
    options: tuple[_SelectionType, ...]
    _cursor: int

    # send the selection to the model for handling by the callback implementor
    _update_model: Callable[[int], bool]

    # called to trigger the view update after next or prev call, since
    # the current selection has changed
    _update_view: Callable[[], None]

    def __init__(self, options: tuple[_SelectionType, ...], default=None):
        self.options = options
        self._update_view = lambda: None

        if default not in range(len(options)):
            self._cursor = 0
        else:
            self._cursor = default

        self._update_model = lambda _: False

    def set_confirmation(self, callback: Callable) -> Self:
        """
        Allows the calling scope to provide the callback which is invoked
        on confirmation of the selection. The argument passed to the callback
        is the selection cursor, this is an integer in range(0, len(options)).
        Args:
            callback: called on confirm. Dropped if it returns true, held otherwise

        Returns: Self, i.e. a fluent interface

        """
        self._update_model = callback
        return self

    def set_on_change_selection(
        self, on_change: Callable[[], None], call_now=True
    ) -> Self:
        """
        Sets a callback to be invoked with no args each time the selection is changed
        using the next and prev methods
        Args:
            on_change: the callback
            call_now: whether to call it once on setting it

        Returns: Self: i.e. a fluent interface

        """
        self._update_view = on_change
        if call_now:
            on_change()
        return self

    def next(self):
        self._cursor = (self._cursor + 1) % len(self.options)
        self._update_view()

    def prev(self):
        self._cursor = (self._cursor - 1) % len(self.options)
        self._update_view()

    def select(self, index: int):
        self._cursor = index % len(self.options)

    def current(self) -> _SelectionType:
        return self.options[self._cursor]

    def _confirm(self, cursor: int) -> bool:
        """
        Returns: bool, indicates if the callback was dropped by the selection. If
        the callback returns True, it is replaced with the default trivial callback
        """
        if self._update_model and self._update_model(cursor):
            self._update_model = lambda _: False
            return True

        return False

    def confirm(self) -> bool:
        """
        Returns: bool, indicates if the callback was dropped by the selection. If
        the callback returns True, it is replaced with the default trivial callback
        """
        return self._confirm(self._cursor)


class GridSelection(Selection[_SelectionType]):
    options: tuple[tuple[_SelectionType | None, ...], ...]
    _opt_sequence: Sequence[_SelectionType]
    _index_map: tuple[int, ...]
    _cursor: tuple[int, int]
    _dimensions: tuple[int, int]

    def __init__(
        self,
        options: Sequence[_SelectionType],
        key: Callable[[_SelectionType], tuple[int, int]],
    ):
        option_map: dict[tuple[int, int], _SelectionType] = {
            key(opt): opt for opt in options
        }
        self._opt_sequence = options

        all_x = [k[0] for k in option_map.keys()]
        all_y = [k[1] for k in option_map.keys()]
        x_span = (max(all_x) + 1, min(all_x))
        y_span = (max(all_y) + 1, min(all_y))
        bottom = y_span[1]
        left = x_span[1]

        self._index_map: dict[tuple[int, int], int] = {
            (key(opt)[0] - left, key(opt)[1] - bottom): idx
            for idx, opt in enumerate(options)
        }

        self._dimensions = (x_span[0] - x_span[1], y_span[0] - y_span[1])

        self.options = tuple(
            tuple(
                option_map.get((x + left, y + bottom))
                for x in range(self._dimensions[0])
            )
            for y in range(self._dimensions[1])
        )
        self._cursor = (0, 0)
        if self.current() is None:
            self._increment_cursor(0, 1)

    def _increment_cursor(self, idx: int, amount: int):
        sign = round(amount / abs(amount))
        add: tuple[int, int] = (1 * sign, 0) if idx == 0 else (0, 1 * sign)
        amount_left = abs(amount)
        while amount_left > 0:
            self._cursor = (
                (self._cursor[0] + add[0]) % len(self.options),
                (self._cursor[1] + add[1]) % len(self.options[self._cursor[0]]),
            )

            if self.options[self._cursor[0]][self._cursor[1]] is not None:
                amount_left -= 1

    def left(self):
        self._increment_cursor(0, -1)
        self._update_view()

    def right(self):
        self._increment_cursor(0, 1)
        self._update_view()

    def up(self):
        self._increment_cursor(1, 1)
        self._update_view()

    def down(self):
        self._increment_cursor(1, -1)
        self._update_view()

    def next(self):
        old_x = self._cursor[0]
        self.right()
        if self._cursor[0] <= old_x:
            self.up()

    def prev(self):
        old_x = self._cursor[0]
        self.left()
        if self._cursor[0] > old_x:
            self.down()

    def current(self) -> _SelectionType | None:
        return self.options[self._cursor[0]][self._cursor[1]]

    def _confirm(self, cursor: tuple[int, int]) -> bool:
        if self._update_model and self._update_model(
            self._opt_sequence.index(self.current())
        ):
            self._update_model = lambda _: False
            return True

        return False


class BaseInputMode:
    next_mode: Self
    mode: int
    name: str = ""

    def __init__(self, view, next_mode=None):
        self.view = view
        self.next_mode = next_mode or self

    def get_name(self) -> str:
        return self.name or "no name"

    def enable(self):
        pass

    def disable(self):
        pass

    def set_next_mode(self, mode: Self) -> Self:
        self.next_mode = mode
        return self

    def get_next_mode(self) -> Self:
        return self.next_mode

    def on_key_press(self, symbol: int, modifiers: int):
        pass

    def on_key_release(self, symbol: int, modifiers: int):
        pass
