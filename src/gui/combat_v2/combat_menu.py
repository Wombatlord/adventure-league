from typing import Callable

from src.entities.action.actions import (
    AttackAction,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.gui.combat.node_selection import NodeSelection
from src.gui.combat_v2.types import Highlighter
from src.gui.components.menu import LeafMenuNode, Menu, MenuNode, SubMenuNode
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


def move_choice(
    available_moves: list[dict], get_current_node, on_teardown, highlighter: Highlighter
) -> MenuNode:
    moves = available_moves
    callbacks_by_destination = {
        move["subject"][-1]: move["on_confirm"] for move in moves
    }
    templates_by_destination = {move["subject"][-1]: move["subject"] for move in moves}

    def choose_move(node: Node):
        callback = callbacks_by_destination.get(node, lambda: None)
        callback()
        on_teardown()

    def validate_move(node: Node) -> bool:
        return node in callbacks_by_destination

    def show_path(node: Node) -> None:
        current = templates_by_destination.get(node, [node, node])
        highlighter.highlight(
            green=current[:1],
            gold=current[1:-1],
            red=current[-1:],
        )

    node_selection = NodeSelection(
        on_confirm=choose_move,
        validate_selection=validate_move,
        show_template=show_path,
        clear_templates=highlighter.clear,
        get_current=get_current_node,
        enable_parent_menu=lambda: None,
        keep_last_valid=True,
    )

    return LeafMenuNode(label="Move", on_click=node_selection.enable)


def attack_choice(available_targets: list[dict], on_teardown) -> MenuNode:
    submenu_config = []
    for target in available_targets:
        submenu_config.append(_leaf_from_action_details(target, on_teardown))

    return SubMenuNode("Attack", sub_menu=submenu_config)


def consume_item_choice(available_items: list[dict], on_teardown) -> MenuNode:
    submenu_config = []
    for item in available_items:
        submenu_config.append(_leaf_from_action_details(item, on_teardown))

    return SubMenuNode("Consume Item", sub_menu=submenu_config)


def end_turn_confirmation(details: list[dict], on_teardown) -> MenuNode:
    submenu_config = [
        LeafMenuNode(
            label=details[0].get("label", ""),
            on_click=_call_then_teardown(
                details[0].get("on_confirm", lambda: None), on_teardown
            ),
            closes_menu=True,
        )
    ]
    return SubMenuNode("End Turn", sub_menu=submenu_config)


def from_event(
    event,
    get_current_node: Callable[[], Node],
    on_teardown: Callable[[], None],
    highlighter: Highlighter,
) -> Menu:
    action_types = event.get("choices")
    menu_config: list[MenuNode] = []
    for action_name, action_details in action_types.items():
        menu_node = None
        match action_name:
            case MoveAction.name:
                menu_node = move_choice(
                    action_details, get_current_node, on_teardown, highlighter
                )

            case AttackAction.name:
                menu_node = attack_choice(action_details, on_teardown)

            case ConsumeItemAction.name:
                menu_node = consume_item_choice(action_details, on_teardown)

            case EndTurnAction.name:
                menu_node = end_turn_confirmation(action_details, on_teardown)

        if menu_node:
            menu_config.append(menu_node)


def empty() -> Menu:
    config = []
    menu = Menu(config)
    menu.hide()
    return menu
