from __future__ import annotations

from typing import Callable

import arcade
import arcade.color
import arcade.key

from src.engine.init_engine import eng
from src.entities.actions import MoveAction
from src.gui.components import combat_menu
from src.gui.components.buttons import end_turn_button
from src.gui.components.input_capture import BaseInputMode, GridSelection, Selection
from src.gui.components.menu import Menu
from src.gui.sections.combat_sections import CombatGridSection
from src.gui.sections.command_bar import CommandBarSection
from src.gui.window_data import WindowData
from src.utils.functional import call_in_order
from src.world.node import Node


class ActionSelectionInputMode(BaseInputMode):
    name: str
    enabled = False

    def __init__(self, view: CombatView, selection: Selection, name: str):
        self.selection = selection
        self.name = name
        self.view = view

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.UP:
                self.selection.prev()
            case arcade.key.DOWN:
                self.selection.next()
            case arcade.key.SPACE:
                self.selection.confirm()


class GridSelectionMode(ActionSelectionInputMode):
    name: str
    selection: GridSelection[tuple[Node, ...]]

    def __init__(
        self,
        view: CombatView,
        parent: Menu,
        selection: GridSelection[tuple[Node, ...]],
        name: str,
    ):
        super().__init__(view, selection, name)
        self.parent = parent
        self.enabled = False

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def on_key_press(self, symbol: int, modifiers: int):
        if not self.enabled:
            return

        match symbol:
            case arcade.key.ESCAPE:
                self.disable()
                self.parent.show()
                self.view.combat_grid_section.hide_path()
            case arcade.key.UP:
                self.selection.up()
            case arcade.key.DOWN:
                self.selection.down()
            case arcade.key.LEFT:
                self.selection.left()
            case arcade.key.RIGHT:
                self.selection.right()
            case arcade.key.SPACE:
                self.selection.confirm()


class NoSelection:
    enabled = False
    options = "no options"


class NoInputMode(BaseInputMode):
    name = "no input"
    selection = NoSelection


class CombatView(arcade.View):
    input_mode: BaseInputMode
    selection: GridSelection | None

    def __init__(self, parent_factory: Callable[[], arcade.View]):
        super().__init__()
        self.parent_factory = parent_factory

        self.combat_grid_section = CombatGridSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=WindowData.height,
            prevent_dispatch_view={False},
        )

        # CommandBar config
        self.buttons = [
            end_turn_button(
                lambda _: self.input_mode.on_key_press(arcade.key.SPACE, 0)
            ),
        ]

        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        self.selections = {}
        self.item_menu_mode_allowed = True
        self.input_modes = {}
        self.input_mode = NoInputMode(self)
        self._default_input_mode = None
        self.confirm_selection = lambda: None
        self.selection = None
        self.add_section(self.command_bar_section)
        self.add_section(self.combat_grid_section, at_draw_order=-1)
        self.combat_menu: Menu | None = None
        eng.init_combat()

    def on_show_view(self):
        self.command_bar_section.manager.enable()
        eng.combat_dispatcher.volatile_subscribe(
            topic="await_input",
            handler_id="BattleView.set_input_request",
            handler=self.set_action_selection,
        )

    def on_draw(self):
        self.combat_grid_section.combat_menu = self.combat_menu

    def reset_input_mode(self):
        self.input_mode = NoInputMode(self)

    def set_action_selection(self, event):
        if requester := event.get("await_input"):
            if requester.owner.ai:
                return
        self.setup_combat_menu(event)
        eng.await_input()
        self.selection = GridSelection(
            event["choices"][MoveAction.name], key=lambda o: o["subject"][-1][:2]
        )

        self.selection.set_on_change_selection(
            call_in_order(
                (
                    lambda: self.combat_grid_section.show_path(
                        self.selection.current()["subject"]
                    ),
                    lambda: self.combat_grid_section.show_mouse_sprite(),
                )
            ),
            call_now=False,
        ).set_confirmation(
            # this is a negated cast to bool bc we want to return True
            lambda _: ~bool(
                call_in_order(
                    (
                        self.selection.current()["on_confirm"],
                        lambda: self.combat_grid_section.hide_path(),
                        lambda: self.combat_grid_section.hide_mouse_sprite(),
                        lambda: self.combat_grid_section.reset_mouse_selection(),
                        lambda: self.combat_grid_section.disarm_click(),
                        lambda: self.reset_input_mode(),
                        lambda: eng.input_received(),
                    )
                )()
            )
        )
        self.combat_grid_section.provide_mouse_selection(
            lambda n: self.input_mode.enabled and self.selection.select(*n[:2])
        )

        self.input_mode = GridSelectionMode(
            self, self.combat_menu, self.selection, "move"
        )

    def setup_combat_menu(self, event):
        self.combat_menu = combat_menu.build_from_event(
            event,
            (self.window.width * 0.75, self.window.height * 0.75),
            on_teardown=lambda: eng.input_received(),
            submenu_overrides={
                MoveAction.name: call_in_order(
                    (
                        lambda: self.combat_menu.hide(),
                        lambda: self.input_mode.enable(),
                        lambda: self.combat_grid_section.show_path(
                            self.selection.current()["subject"]
                        ),
                        lambda: self.combat_grid_section.show_mouse_sprite(),
                        lambda: self.combat_grid_section.arm_click(
                            lambda: self.selection.confirm() or None
                        ),
                    )
                )
            },
        )
        self.combat_menu.enable()

    def on_key_release(self, _symbol: int, _modifiers: int):
        if not self.combat_grid_section.cam_controls.on_key_release(_symbol):
            return

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        print(f"{self.__class__}.on_key_press called with '{symbol}'")
        if not self.combat_grid_section.cam_controls.on_key_press(symbol):
            return

        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    self.window.show_view(self.parent_factory())

        self.input_mode.on_key_press(symbol, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
