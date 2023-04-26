from __future__ import annotations

import math
from types import FunctionType
from typing import Callable, NamedTuple, Self

import arcade
from arcade.gui import UIAnchorLayout, UIBoxLayout, UIEvent, UIManager, UITextureButton
from pyglet.math import Vec2

from src.gui.animation.positioning import maintain_position
from src.gui.combat.node_selection import NodeSelection
from src.gui.components.buttons import nav_button, update_button
from src.gui.ui_styles import ADVENTURE_STYLE, UIStyle
from src.gui.window_data import WindowData
from src.textures.texture_text import TextureText

# DATA STRUCTURES
ExecutableMenuItem = tuple[str, Callable[[UIEvent], None]]


class MenuNode(NamedTuple):
    label: str
    content: ExecutableMenuItem | list[Self]


class MenuNode:
    label: str

    def get_click_handler(self, ctx: Menu) -> Callable[[], None]:
        pass


class LeafMenuNode(MenuNode):
    closes_menu: bool

    def __init__(
        self, label: str, on_click: Callable[[], None], closes_menu: bool = False
    ):
        self.label = label
        self._on_click = on_click
        self.closes_menu = closes_menu

    def get_click_handler(self, ctx: Menu) -> Callable[[], None]:
        if self.closes_menu:
            return ctx.closing_action(self._on_click)

        return self._on_click


class SubMenuNode(MenuNode):
    on_click: Callable[[], None]

    def __init__(self, label: str, sub_menu: list[MenuNode]) -> None:
        self.label = label
        self._sub_menu_config = sub_menu

    def get_click_handler(self, ctx: Menu) -> Callable[[], None]:
        return lambda: ctx.enter_submenu(self._sub_menu_config)


class NodeSelectionNode(MenuNode):
    def __init__(self, label: str, node_selection: NodeSelection) -> None:
        self.label = label
        self._node_selection = node_selection

    def get_click_handler(self, ctx: Menu) -> Callable[[], None]:
        self._node_selection.set_enable_parent_menu(ctx.enable)
        return self._node_selection.enable


SubMenu = list[ExecutableMenuItem]
MenuWithSubMenu = tuple[str, SubMenu]
MenuSchema = list[MenuNode]


class ButtonRegistry(NamedTuple):
    update = update_button
    navigate = nav_button


ButtonCallback = Callable[[], None]
ButtonFactory = Callable[[ButtonCallback, str], UITextureButton]


# LE MENU
class Menu:
    manager: UIManager | None
    main_box: UIBoxLayout | None
    _factory = lambda *_: update_button

    def set_factory(self, factory: ButtonFactory):
        self._factory = lambda *_: factory

    def button_factory(self, action, label) -> UITextureButton:
        factory = self._factory()
        return factory(action, label)

    def __init__(
        self,
        menu_config: MenuSchema,
        pos: tuple[int, int],
        area: tuple[int, int],
        button_style: UIStyle | None = None,
        align: str = "center",
    ) -> None:
        self.align = align
        self.full_menu_graph = menu_config
        self.current_menu_graph = menu_config
        self.x, self.y = pos
        self.width, self.height = area
        self.manager = None
        self.anchor = None
        self.main_box = None
        self.anchor = None
        self.button_style = button_style or ADVENTURE_STYLE
        self.sprite_list = arcade.SpriteList()
        self._buttons = []
        self._setup()

    @property
    def size(self) -> tuple[int, int]:
        return self.anchor.width, self.anchor.height

    def _setup(self):
        if self.manager:
            self.manager.clear()
        else:
            self.manager = UIManager()

        self.sprite_list.clear()
        self.anchor = UIAnchorLayout(
            width=self.width, height=self.height, size_hint=(None, None)
        )
        self.anchor.center = self.x, self.y
        self.manager.add(self.anchor).with_border(color=arcade.color.RED)
        self.main_box = UIBoxLayout(
            size_hint=(1, 1),
            space_between=2,
        ).with_border(width=3, color=arcade.color.BLUE)

        self.anchor.add(self.main_box, anchor_x=self.align)
        self.build_menu(self.current_menu_graph)

    def disable(self):
        self.manager.disable()
        self.manager.clear()

    def enable(self):
        self._setup()
        self.manager.enable()
        self.draw()

    def show(self):
        self.anchor.center = self.x, self.y
        self.position_labels()

    def hide(self):
        self.anchor.center = -self.x, -self.y
        self.position_labels()

    def update(self):
        self.anchor.center = self.x, self.y
        self.manager.on_update(1 / 60)
        self.position_labels()

    def draw(self):
        if self.manager._enabled:
            self.manager.draw()
            self.sprite_list.draw(pixelated=True)

    def is_enabled(self) -> bool:
        return self.manager._enabled

    def maintain_menu_positioning(self, width, height):
        self.anchor.center = maintain_position(
            v1=(WindowData.width, WindowData.height), v2=(width, height), thing=self
        )

    def build_menu(self, menu: MenuSchema):
        self._buttons = []
        for node in menu:
            if not isinstance(node, MenuNode):
                raise TypeError(f"node {repr(node)} was not a MenuNode")

            action = node.get_click_handler(self)
            btn = update_button(action, "")
            self._buttons.append(btn)

            text = TextureText.create(
                text=node.label,
                start_x=0,
                lines=1,
                font_name=WindowData.font,
                font_size=27,
            )
            self.sprite_list.append(text.sprite)

            btn.size_hint = (1, None)
            btn.resize(height=50)
            btn.style = self.button_style
            self.main_box.add(btn)

        self.position_labels()

    def position_labels(self):
        for btn, sprite in zip(self._buttons, self.sprite_list):
            sprite.center_x, sprite.center_y = btn.center_x, btn.center_y + 10

    def closing_action(self, action: Callable[[], None]) -> Callable[[], None]:
        def _do_then_close():
            action()
            self.disable()

        return _do_then_close

    def derive_button_action_from_content(
        self,
        content: Callable[[UIEvent], None] | list,
        *options,
    ) -> Callable[[UIEvent], None]:
        action = None

        match content:
            case func if isinstance(func, Callable | FunctionType):
                action = func

            case sub_menu if isinstance(sub_menu, list):
                action = self.open_sub_menu_action(sub_menu=sub_menu)

            case _:
                raise TypeError(
                    f"{content} should be Callable, SubMenu, or arcade.View. Got {type(content)=}"
                )

        if options and options[0]:
            action = self.closing_action(action)

        return action

    def open_sub_menu_action(self, sub_menu) -> Callable[[UIEvent], None]:
        def _on_click() -> None:
            self.enter_submenu(sub_menu)

        return _on_click

    def enter_submenu(self, menu: MenuSchema):
        self.current_menu_graph = menu
        self._setup()

        if self.current_menu_graph == self.full_menu_graph:
            return

        self.add_return_to_top_level_button()
    def add_return_to_top_level_button(self):
        btn = update_button(
            on_click=lambda: self.enter_submenu(self.full_menu_graph), text="Return"
        )
        btn.resize(height=50)
        btn.style = ADVENTURE_STYLE
        btn.size_hint = (1, None)
        self.main_box.add(btn)
