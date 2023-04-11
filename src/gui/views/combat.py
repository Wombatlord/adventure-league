from __future__ import annotations

from typing import Callable

import arcade
import arcade.color
import arcade.key

from src.engine.init_engine import eng
from src.entities.actions import MoveAction
from src.gui.components.buttons import end_turn_button
from src.gui.components.input_capture import BaseInputMode, GridSelection, Selection
from src.gui.sections.combat_sections import CombatGridSection
from src.gui.sections.command_bar import CommandBarSection
from src.gui.window_data import WindowData
from src.world.node import Node


class ActionSelectionInputMode(BaseInputMode):
    name: str

    def __init__(self, view: CombatView, selection: Selection, name: str):
        self.selection = selection
        self.name = name
        self.view = view

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.TAB:
                self.view.next_input_mode()
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
        self, view: CombatView, selection: GridSelection[tuple[Node, ...]], name: str
    ):
        super().__init__(view, selection, name)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.TAB:
                self.view.next_input_mode()
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
    options = "no options"


class NoInputMode(BaseInputMode):
    name = "no input"
    selection = NoSelection


class CombatView(arcade.View):
    input_mode: BaseInputMode
    selections: dict[str, Selection]

    def __init__(self, parent_factory: arcade.View):
        super().__init__()
        self.parent_factory = parent_factory

        self.combat_grid_section = CombatGridSection(
            left=0,
            bottom=WindowData.height / 2,
            width=WindowData.width,
            height=WindowData.height / 2,
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
        self.bind_input_modes()
        self.add_section(self.command_bar_section)
        self.add_section(self.combat_grid_section)
        eng.init_combat()

    def bind_input_modes(self):
        if not self.selections:
            self.input_mode = NoInputMode(self)
            return

        self.input_modes = {}
        prev_name = None
        for name, selection in sorted(
            self.selections.items(), key=lambda s: int(s[0] != MoveAction.name)
        ):
            input_mode_class = (
                GridSelectionMode
                if name == MoveAction.name
                else ActionSelectionInputMode
            )
            self.input_modes[name] = input_mode_class(self, selection, name)
            if prev_name:
                self.input_modes[name].set_next_mode(self.input_modes[prev_name])
            prev_name = name

        self.input_modes[MoveAction.name].set_next_mode(self.input_modes[prev_name])
        self._default_input_mode = self.input_modes[MoveAction.name]
        self.reset_input_mode()

    def next_input_mode(self):
        self.input_mode = self.input_mode.get_next_mode()

    def reset_input_mode(self):
        self.input_mode = self._default_input_mode

    def on_show_view(self):
        self.command_bar_section.manager.enable()
        eng.combat_dispatcher.volatile_subscribe(
            topic="await_input",
            handler_id="BattleView.set_input_request",
            handler=self.set_action_selection,
        )

    def on_draw(self):
        pass

    def make_on_confirm(self, options, hide_stuff) -> Callable[[int], bool]:
        def on_confirm(opt_idx: int) -> bool:
            hide_stuff()
            self.reset_input_mode()
            eng.input_received()
            return options[opt_idx]["on_confirm"]()

        return on_confirm

    def set_action_selection(self, event):
        if requester := event.get("await_input"):
            if requester.owner.ai:
                return
        self.combat_grid_section.setup_combat_menu(event)
        eng.await_input()

        choices = event.get("choices")
        selections = {}
        no_op = lambda: None

        for name, options in choices.items():
            if not options:
                continue

            hide_stuff = no_op
            if name == MoveAction.name:
                hide_stuff = lambda: self.combat_grid_section.hide_path()

            _on_confirm = self.make_on_confirm(options, hide_stuff)

            kwargs = {"options": tuple(opt["subject"] for opt in options)}
            if name == MoveAction.name:
                selection_class = GridSelection
                kwargs["key"] = lambda opt: tuple(opt[-1][:2])
            else:
                selection_class = Selection

            selections[name] = selection_class(
                **kwargs,
            ).set_confirmation(_on_confirm)

            update_selection = no_op
            if name == MoveAction.name:
                update_selection = lambda: self.combat_grid_section.show_path(
                    selections[MoveAction.name].current()
                )

            selections[name].set_on_change_selection(update_selection)
        self.selections = selections
        self.bind_input_modes()

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
