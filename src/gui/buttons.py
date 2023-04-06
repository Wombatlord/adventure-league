from typing import Callable

import arcade
from arcade import get_window
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton, UITextureButton

from src.engine.init_engine import eng
from src.gui.states import ViewStates
from src.textures.texture_config import (
    TextureButtonNinePatchConfig,
    load_ui_texture_button,
)


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


def get_nav_handler(target: type[arcade.View] | arcade.View) -> UIEventHandler:
    """An UIEventHandler which changes the View.

    Args:
        target (type[arcade.View]): The target View to switch to, received from the UIFlatButton this handler is attached to.

    Returns:
        UIEventHandler: An implementation of a handler for a UIEvent (eg. on_click, on_keypress etc.)
    """

    def _handle(event: UIEvent | None = None):
        destination = target if isinstance(target, arcade.View) else target()
        get_window().show_view(destination)

    return _handle


def nav_button(
    target: Callable[[], arcade.View] | type[arcade.View] | arcade.View, text: str
) -> UITextureButton:
    """A generic button for changing to a different View.

    Args:
        target (type[arcade.View]): The target View to change to, passed to the click handler of the button.
        text (str): The text to render on the button, typically the name of the view that will be displayed on click.

    Returns:
        UITextureButton: A button with a text label and an attached click handler.
    """
    btn = load_ui_texture_button(
        texture_config=TextureButtonNinePatchConfig.gold(), text=text
    )
    btn.on_click = get_nav_handler(target)

    return btn


def get_new_missions_handler(event: UIEvent) -> UIEventHandler:
    eng.refresh_mission_board()


def get_new_missions_button() -> UITextureButton:
    btn = load_ui_texture_button(
        texture_config=TextureButtonNinePatchConfig.gold(), text="New Missions"
    )
    btn.on_click = get_new_missions_handler

    return btn


def get_switch_to_recruitment_pane_handler(view) -> UIEventHandler:
    """
    Do any necessary reconfiguration of recruitment_pane_section when switching to this section from the roster and team display.
    Ensures the section has appropriate window size values if the window was resized while recruitment section was disabled.
    Assigns the correct buttons to the command bar for this section.

    Attached to self.recruit_button as click_handler or called directly in on_key_press.
    """

    def _handle(event: UIEvent = None):
        view.state = ViewStates.RECRUIT

        # Disable the roster_and_team_pane_section
        view.roster_and_team_pane_section.enabled = False
        view.roster_and_team_pane_section.manager.disable()

        # view.recruitment_pane_section.set_guild_funds_label()
        view.recruitment_pane_section.update_ui()
        view.recruitment_pane_section.manager.enable()
        view.recruitment_pane_section.enabled = True

        # Set up CommandBar with appropriate buttons
        view.command_bar_section.manager.disable()
        view.command_bar_section.buttons = view.recruitment_pane_buttons
        view.command_bar_section.flush()
        view.command_bar_section.manager.enable()

    return _handle


def get_switch_to_roster_and_team_panes_handler(view) -> UIEventHandler:
    """
    Do any necessary reconfiguration of roster_and_team_pane_section when switching to this section from the recruitment display.
    Ensures the section has appropriate window size values if the window was resized while roster_and_team_pane_section was disabled.
    Assigns the correct buttons to the command bar for this section.

    Attached to self.roster_button as click_handler and called directly in on_key_press.
    """

    def _handle(event: UIEvent = None):
        view.state = ViewStates.ROSTER
        # Disable the recruitment_pane_section
        view.recruitment_pane_section.enabled = False

        # Flush and setup the section so that new recruits are present and selectable via the UIManager
        view.roster_and_team_pane_section.update_ui()
        view.roster_and_team_pane_section.manager.enable()
        view.roster_and_team_pane_section.enabled = True

        # Setup CommandBarSection with appropriate buttons
        view.command_bar_section.manager.disable()
        view.command_bar_section.buttons = view.roster_pane_buttons
        view.command_bar_section.flush()
        view.command_bar_section.manager.enable()

    return _handle


def recruit_button(view) -> UITextureButton:
    """Attached Handler will change from displaying the roster & team panes
    to showing recruits available for hire, with the appropriate command bar.

    Returns:
        UIFlatButton: Button with attached handler.
    """
    btn = load_ui_texture_button(
        texture_config=TextureButtonNinePatchConfig.gold(), text="Recruit"
    )
    btn.on_click = get_switch_to_recruitment_pane_handler(view)
    return btn


def roster_button(view) -> UITextureButton:
    """Attached Handler will change from displaying the roster & team panes
    to showing recruits available for hire, with the appropriate command bar.

    Returns:
        UIFlatButton: Button with attached handler.
    """
    btn = load_ui_texture_button(
        texture_config=TextureButtonNinePatchConfig.gold(), text="Roster"
    )
    btn.on_click = get_switch_to_roster_and_team_panes_handler(view)
    return btn


def get_end_turn_handler(view) -> UIEventHandler:
    def _handle(event: UIEvent):
        if not view.target_selection and eng.awaiting_input:
            eng.input_received()
            return

        if not view.target_selection:
            return

        ok = view.target_selection.confirm()
        if ok:
            view.combat_grid_section.hide_path()
            view.target_selection = None
            view.item_menu_mode_allowed = True

    return _handle


def end_turn_button(on_click) -> UITextureButton:
    btn = load_ui_texture_button(
        texture_config=TextureButtonNinePatchConfig.gold(), text="Click me to Advance!"
    )
    btn.on_click = on_click

    return btn
