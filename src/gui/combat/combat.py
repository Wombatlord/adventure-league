from __future__ import annotations

from typing import Callable
from weakref import WeakMethod

import arcade
import arcade.color
import arcade.key

from src.engine.init_engine import eng
from src.entities.action.actions import MoveAction
from src.entities.magic.caster import MagicAction
from src.gui.combat import combat_menu
from src.gui.combat.combat_sections import CombatGridSection
from src.gui.combat.node_selection import NodeSelection
from src.gui.components.buttons import end_turn_button
from src.gui.components.input_capture import BaseInputMode, GridSelection, Selection
from src.gui.components.menu import Menu
from src.gui.generic_sections.command_bar import CommandBarSection
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
        self._on_esc = None
        self.node_change_callback = None
        eng.init_combat()

    def on_show_view(self):
        self.command_bar_section.manager.enable()
        eng.combat_dispatcher.volatile_subscribe(
            topic="await_input",
            handler_id="BattleView.set_input_request",
            handler=self.set_action_selection,
        )

    def on_draw(self):
        self.clear()
        self.combat_grid_section.combat_menu = self.combat_menu

    def reset_input_mode(self):
        self.input_mode = NoInputMode(self)

    def set_action_selection(self, event):
        if requester := event.get("await_input"):
            if requester.owner.ai:
                return
        self.setup_combat_menu(event)
        eng.await_input()

    def set_on_esc(self, callback):
        self._on_esc = callback

    def create_move_selection(self, event: dict) -> NodeSelection:
        moves = event["choices"][MoveAction.name]
        callbacks_by_destination = {
            move["subject"][-1]: move["on_confirm"] for move in moves
        }
        templates_by_destination = {
            move["subject"][-1]: move["subject"] for move in moves
        }

        def choose_move(node: Node):
            callback = callbacks_by_destination.get(node, lambda: None)
            callback()
            eng.input_received()
            self.node_change_callback = None

        def validate_move(node: Node) -> bool:
            return node in callbacks_by_destination

        def show_template(node: Node):
            self.combat_grid_section.show_path(templates_by_destination.get(node, []))

        return NodeSelection(
            on_confirm=choose_move,
            validate_selection=validate_move,
            show_template=show_template,
            clear_templates=self.combat_grid_section.hide_highlight,
            get_current=self.combat_grid_section.get_mouse_node,
            enable_parent_menu=self.enable_combat_menu,
            keep_last_valid=True,
        )

    def setup_combat_menu(self, event):
        node_selection = self.create_move_selection(event)

        def on_esc():
            node_selection.disable()
            self.node_change_callback = None

        def submenu_override() -> bool:
            node_selection.enable()
            self.node_change_callback = node_selection.on_selection_changed
            self.set_on_esc(on_esc)
            self.combat_grid_section.arm_click(node_selection.on_selection_confirmed)
            return True

        self.combat_menu = combat_menu.build_from_event(
            event,
            (self.window.width * 0.75, self.window.height * 0.75),
            on_teardown=lambda: eng.input_received(),
            submenu_overrides={MoveAction.name: (submenu_override, True)},
        )
        self.combat_menu.enable()

    def enable_combat_menu(self):
        self.combat_menu.enable()

    def on_hovered_node_change(self):
        if self.node_change_callback is not None:
            self.node_change_callback()

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

            case arcade.key.ESCAPE:
                if self._on_esc:
                    self._on_esc()
                    self._on_esc = None

        self.input_mode.on_key_press(symbol, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.combat_menu.maintain_menu_positioning(width=width, height=height)
        self.combat_menu.position_labels()
        WindowData.width = width
        WindowData.height = height
