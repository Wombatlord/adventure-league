from typing import Callable, Generic, TypeVar

_SelectionType = TypeVar("_SelectionType", bound=object)


class Selection(Generic[_SelectionType]):
    options: tuple[_SelectionType, ...]
    _cursor: int
    _callback: Callable[[int], bool]

    def __init__(self, options: tuple[_SelectionType, ...]):
        self.options = options
        self._cursor = 0
        self._callback = lambda _: False

    def set_confirmation(self, callback: Callable):
        self._callback = callback

    def next(self):
        self._cursor = (self._cursor + 1) % len(self.options)

    def prev(self):
        self._cursor = (self._cursor - 1) % len(self.options)

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
