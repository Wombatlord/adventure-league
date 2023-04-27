from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Self

import arcade

if TYPE_CHECKING:
    from src.gui.combat_v2.scene import Scene

from src.entities.action.actions import (
    AttackAction,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.magic.caster import MagicAction
from src.gui.combat.node_selection import NodeSelection
from src.gui.components.menu import (
    LeafMenuNode,
    Menu,
    MenuNode,
    NodeSelectionNode,
    SubMenuNode,
)
from src.utils.rectangle import Rectangle
from src.world.node import Node


def _call_then_teardown(callback, on_teardown):
    def _callback():
        callback()
        on_teardown()

    return _callback


def _leaf_from_action_details(details: dict, on_teardown: Callable):
    return LeafMenuNode(
        label=details.get("label", ""),
        on_click=_call_then_teardown(
            callback=details.get("on_confirm", lambda: None), on_teardown=on_teardown
        ),
    )


_TRIVIAL_TEARDOWN = lambda: None
_TRIVIAL_HIGHLIGHT = lambda *_: None


class CombatMenu:
    _menu: Menu
    _scene: Scene
    _move_selection: NodeSelection | None
    _on_teardown: Callable[[], None]
    _highlight: Callable[
        [
            list[Node],
        ],
        None,
    ]
    _menu_rect: Rectangle | None

    @classmethod
    def empty(cls) -> Self:
        config = []
        menu = Menu(
            config,
            pos=(arcade.get_window().width * 0.75, arcade.get_window().height * 0.75),
            area=(250, 50),
        )
        menu.hide()
        return cls(menu=menu)

    def __init__(self, menu: Menu | None = None, scene: Scene | None = None):
        self._menu = menu
        self._scene = scene
        self._on_teardown = _TRIVIAL_TEARDOWN
        self._highlight = _TRIVIAL_HIGHLIGHT
        self._move_selection = None
        self._menu_rect = None

    @property
    def menu(self):
        return self._menu

    @property
    def move_selection(self) -> NodeSelection:
        return self._move_selection

    def is_selecting_move(self) -> bool:
        if not self._move_selection:
            return False

        return self._move_selection.enabled

    def set_on_teardown(self, on_teardown: Callable) -> Self:
        self._on_teardown = on_teardown
        if self._move_selection:
            self._move_selection.set_on_teardown(on_teardown)
        return self

    def set_highlight(
        self,
        highlight_nodes: Callable[
            [
                list[Node],
            ],
            None,
        ],
    ):
        self._highlight = highlight_nodes
        return self

    def set_menu_rect(self, rect: Rectangle) -> Self:
        self._menu_rect = rect
        if self._menu:
            self._menu.x = rect.x
            self._menu.y = rect.y
            self._menu.height = rect.h
            self._menu.width = rect.w
            self._menu.update()

        return self

    def build(self, event) -> Self:
        if (
            self._on_teardown is _TRIVIAL_TEARDOWN
            or self._highlight is _TRIVIAL_HIGHLIGHT
        ):
            raise ValueError(
                "Make sure the highlight and teardown callbacks have been populated"
            )

        action_types = event.get("choices")
        menu_config: list[MenuNode] = []
        for action_name, action_details in action_types.items():
            menu_node = None
            match action_name:
                case MoveAction.name:
                    menu_node = self.move_choice(
                        action_details,
                        self._scene.get_mouse_node,
                    )

                case AttackAction.name:
                    menu_node = self.attack_choice(action_details)

                case MagicAction.name:
                    menu_node = self.magic_choice(action_details)

                case ConsumeItemAction.name:
                    menu_node = self.consume_item_choice(action_details)

                case EndTurnAction.name:
                    menu_node = self.end_turn_confirmation(action_details)

            if menu_node:
                menu_config.append(menu_node)

        self._menu = Menu(
            menu_config=menu_config,
            pos=self._menu_rect.bottom_left,
            area=self._menu_rect.dims,
            align="right",
        )

        return self

    def move_choice(self, available_moves: list[dict], get_current_node) -> MenuNode:
        moves = available_moves
        callbacks_by_destination = {
            move["subject"][-1]: move["on_confirm"] for move in moves
        }
        templates_by_destination = {
            move["subject"][-1]: move["subject"] for move in moves
        }

        def choose_move(node: Node):
            callback = callbacks_by_destination.get(node, lambda: None)
            callback()
            self._on_teardown()

        def validate_move(node: Node) -> bool:
            return node in callbacks_by_destination

        def show_path(node: Node) -> None:
            current = templates_by_destination.get(node, [node, node])
            self._highlight(
                green=current[:1],
                gold=current[1:-1],
                red=current[-1:],
            )

        self._move_selection = NodeSelection(
            on_confirm=choose_move,
            validate_selection=validate_move,
            show_template=show_path,
            get_current=get_current_node,
            keep_last_valid=True,
        )

        return NodeSelectionNode(label="Move", node_selection=self._move_selection)

    def attack_choice(self, available_targets: list[dict]) -> MenuNode:
        submenu_config = []
        for target in available_targets:
            submenu_config.append(_leaf_from_action_details(target, self._on_teardown))

        return SubMenuNode("Attack", sub_menu=submenu_config)

    def magic_choice(self, available_spells: list) -> MenuNode:
        submenu_config = []
        for spell in available_spells:
            submenu_config.append(_leaf_from_action_details(spell, self._on_teardown))

        return SubMenuNode("Magic", sub_menu=submenu_config)

    def consume_item_choice(self, available_items: list[dict]) -> MenuNode:
        submenu_config = []
        for item in available_items:
            submenu_config.append(_leaf_from_action_details(item, self._on_teardown))

        return SubMenuNode("Consume Item", sub_menu=submenu_config)

    def end_turn_confirmation(self, details: list[dict]) -> MenuNode:
        submenu_config = [
            LeafMenuNode(
                label=details[0].get("label", ""),
                on_click=_call_then_teardown(
                    details[0].get("on_confirm", lambda: None), self._on_teardown
                ),
                closes_menu=True,
            )
        ]
        return SubMenuNode("End Turn", sub_menu=submenu_config)


def empty() -> CombatMenu:
    return CombatMenu.empty()


def from_event(event, scene):
    return CombatMenu(
        event=event,
        scene=scene,
    )
