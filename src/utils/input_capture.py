from typing import Callable, Generic, TypeVar, Self

_SelectionType = TypeVar("_SelectionType", bound=object)


class Selection(Generic[_SelectionType]):
    options: tuple[_SelectionType, ...]
    _cursor: int
    _callback: Callable[[int], bool]

    def __init__(self, options: tuple[_SelectionType, ...], default=None):
        self.options = options
        self._on_change = lambda: None
        
        if default not in range(len(options)):
            self._cursor = 0
        else:
            self._cursor = default

        self._callback = lambda _: False

    def set_confirmation(self, callback: Callable) -> Self:
        self._callback = callback
        return self

    def set_on_change_selection(self, on_change: Callable[[], None], call_now=True) -> Self:
        self._on_change = on_change
        if call_now:
            on_change()

    def next(self):
        self._cursor = (self._cursor + 1) % len(self.options)
        self._on_change()

    def prev(self):
        self._cursor = (self._cursor - 1) % len(self.options)
        self._on_change()

    def select(self, index: int):
        self._cursor = index % len(self.options)

    @property
    def current(self) -> _SelectionType:
        return self.options[self._cursor]

    def confirm(self) -> bool:
        if self._callback and self._callback(self._cursor):
            self._callback = lambda _: False
            return True

        return False
