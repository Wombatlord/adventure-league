from typing import Callable

import arcade
from arcade import get_window
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton

from src.engine.init_engine import eng


class CommandBarMixin:
    """
    Provides some methods to be implemented in any View which should have a command bar.

    Implementations should compose the buttons with attached handlers, labels, and styling
    ready to be added to the UIManager.
    """

    window: arcade.Window

    @property
    def command_bar(self) -> list[UIFlatButton]:
        ...


UIEventHandler = Callable[[UIEvent], None]


def nav_handler(target: type[arcade.View]) -> UIEventHandler:
    """An UIEventHandler which changes the View.

    Args:
        target (type[arcade.View]): The target View to switch to, received from the UIFlatButton this handler is attached to.

    Returns:
        UIEventHandler: An implementation of a handler for a UIEvent (eg. on_click, on_keypress etc.)
    """

    def _handle(event: UIEvent):
        get_window().show_view(target())

    return _handle


def nav_button(target: type[arcade.View], text: str) -> UIFlatButton:
    """A generic button for changing to a different View.

    Args:
        target (type[arcade.View]): The target View to change to, passed to the click handler of the button.
        text (str): The text to render on the button, typically the name of the view that will be displayed on click.

    Returns:
        UIFlatButton: A button with a text label and an attached click handler.
    """
    btn = UIFlatButton(text=text)
    btn.on_click = nav_handler(target)

    return btn


def get_new_missions_handler(event: UIEvent) -> UIEventHandler:
    eng.refresh_mission_board()


def get_new_missions_button() -> UIFlatButton:
    btn = UIFlatButton(text="New Missions")
    btn.on_click = get_new_missions_handler

    return btn


def end_turn_handler(view) -> UIEventHandler:
    def _handle(event: UIEvent):
        if not view.target_selection and eng.awaiting_input:
            eng.next_combat_action()
            eng.awaiting_input = False
            return

        if not view.target_selection:
            return

        ok = view.target_selection.confirm()
        if ok:
            view.combat_grid_section.hide_path()
            view.target_selection = None
            view.item_menu_mode_allowed = True

    return _handle


def end_turn_button(view) -> UIFlatButton:
    btn = UIFlatButton(text="CLICK ME TO ADVANCE!")
    btn.on_click = end_turn_handler(view)

    return btn
