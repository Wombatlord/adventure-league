from typing import Callable, Generic, Self, TypeVar

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

    @property
    def current(self) -> _SelectionType:
        return self.options[self._cursor]

    def confirm(self) -> bool:
        """
        Returns: bool, indicates if the callback was dropped by the selection. If
        the callback returns True, it is replaced with the default trivial callback
        """
        if self._update_model and self._update_model(self._cursor):
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

    def set_next_mode(self, mode: Self) -> Self:
        self.next_mode = mode
        return self

    def get_next_mode(self) -> Self:
        return self.next_mode

    def on_key_press(self, symbol: int, modifiers: int):
        pass

    def on_key_release(self, symbol: int, modifiers: int):
        pass
