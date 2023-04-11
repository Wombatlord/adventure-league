from typing import Callable, Generic, TypeVar

from arcade.gui import UIWidget

_ObservedType = TypeVar("_ObservedType", bound=object)
_AttachedType = TypeVar("_AttachedType", bound=UIWidget)


class Observer(Generic[_ObservedType, _AttachedType]):
    def __init__(
        self,
        get_observed_state: Callable[[], _ObservedType],
        sync_widget: Callable[[_AttachedType, _ObservedType], None],
    ):
        self.get_observed_state = get_observed_state
        self.sync_widget = sync_widget

    def attach(self, widget: _AttachedType) -> _AttachedType:
        previous_state = self.get_observed_state()

        def _on_update(_: float):
            nonlocal previous_state
            if (current := self.get_observed_state()) != previous_state:
                self.sync_widget(widget, current)
                previous_state = current

        widget.on_update = _on_update

        return widget

    def __call__(self, widget: _AttachedType) -> _AttachedType:
        return self.attach(widget=widget)


def observe(
    get_observed_state: Callable[[], _ObservedType],
    sync_widget: Callable[[_AttachedType, _ObservedType], None],
) -> Observer:
    return Observer[_AttachedType, _ObservedType](
        get_observed_state=get_observed_state,
        sync_widget=sync_widget,
    )
