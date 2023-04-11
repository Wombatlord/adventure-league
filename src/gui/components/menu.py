from types import FunctionType
from typing import Callable, NamedTuple, Self

import arcade
from arcade.gui import UIBoxLayout, UIEvent, UIFlatButton, UIManager

from src.gui.components.buttons import nav_button, update_button
from src.gui.ui_styles import ADVENTURE_STYLE

# DATA STRUCTURES
ExecutableMenuItem = tuple[str, Callable[[UIEvent], None]]


class MenuNode(NamedTuple):
    label: str
    content: ExecutableMenuItem | list[Self]


SubMenu = list[ExecutableMenuItem]
MenuWithSubMenu = tuple[str, SubMenu]
MenuSchema = list[MenuWithSubMenu | ExecutableMenuItem]


class ButtonRegistry(NamedTuple):
    update = 0
    navigate = 1


# LE MENU
class Menu:
    def __init__(
        self, menu_config: MenuSchema, pos: tuple[int, int], area: tuple[int, int]
    ) -> None:
        self.full_menu_graph = menu_config
        self.manager = UIManager()
        self.x, self.y = pos
        self.width, self.height = area
        self.main_box = UIBoxLayout(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            size_hint=(None, None),
        )
        self.manager.add(self.main_box)

    def build_menu(self, menu: MenuSchema):
        self.main_box.clear()

        for label, content, btn_id in menu:
            action = self.derive_button_action_from_content(content)
            match btn_id:
                case 0:
                    btn = update_button(on_click=action, text=label)
                case 1:
                    btn = nav_button(target=action, text=label)
            btn.size_hint = (1, None)
            btn.resize(height=50)
            btn.style = ADVENTURE_STYLE
            self.main_box.add(btn)

    def derive_button_action_from_content(
        self, content: Callable[[UIEvent], None] | list
    ) -> Callable[[UIEvent], None]:
        action = None

        match content:
            case func if isinstance(func, Callable | FunctionType):
                action = func

            case sub_menu if isinstance(sub_menu, list | tuple):
                action = self.open_sub_menu_action(sub_menu=sub_menu)

            case view if issubclass(view, arcade.View):
                action = view

            case _:
                raise TypeError(
                    f"{content} should be Callable, SubMenu, or arcade.View. Got {type(content)=}"
                )

        return action

    def open_sub_menu_action(self, sub_menu) -> Callable[[UIEvent], None]:
        def _on_click() -> None:
            self.enter_submenu(sub_menu)

        return _on_click

    def enter_submenu(self, menu: MenuSchema):
        self.build_menu(menu)
        self.add_return_to_top_level_button()

    def add_return_to_top_level_button(self):
        btn = update_button(
            on_click=lambda: self.build_menu(self.full_menu_graph), text="Return"
        )
        btn.resize(height=50)
        btn.style = ADVENTURE_STYLE
        btn.size_hint = (1, None)
        self.main_box.add(btn)
