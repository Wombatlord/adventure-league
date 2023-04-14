from types import FunctionType
from typing import Callable, NamedTuple, Self

import arcade
from arcade.gui import UIAnchorLayout, UIBoxLayout, UIEvent, UIManager, UITextureButton

from src.gui.components.buttons import nav_button, update_button
from src.gui.ui_styles import ADVENTURE_STYLE, UIStyle
from src.gui.window_data import WindowData
from src.textures.texture_text import TextureText

# DATA STRUCTURES
ExecutableMenuItem = tuple[str, Callable[[UIEvent], None]]


class MenuNode(NamedTuple):
    label: str
    content: ExecutableMenuItem | list[Self]


SubMenu = list[ExecutableMenuItem]
MenuWithSubMenu = tuple[str, SubMenu]
MenuSchema = list[MenuWithSubMenu | ExecutableMenuItem]


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
        should_recenter: bool = False,
    ) -> None:
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
        self._setup()

    def _setup(self):
        if self.manager:
            self.manager.clear()
        else:
            self.manager = UIManager()

        self.anchor = UIAnchorLayout(
            width=self.width, height=self.height, size_hint=(None, None)
        )
        self.anchor.center = self.x, self.y
        self.manager.add(self.anchor).with_border(color=arcade.color.RED)
        self.main_box = UIBoxLayout(
            size_hint=(1, 1),
            space_between=2,
        )

        self.anchor.add(self.main_box)
        print(self.anchor.rect.position)
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

    def draw(self):
        if self.manager._enabled:
            self.manager.draw()
            self.sprite_list.draw(pixelated=True)

    def is_enabled(self) -> bool:
        return self.manager._enabled

    def build_menu(self, menu: MenuSchema):
        # self.main_box.clear()
        self.sprite_list.clear()

        for label, content, *options in menu:
            if not isinstance(label, str):
                raise TypeError(f"label must be a string, got {type(label)=}")
            if not callable(content) and not isinstance(content, list):
                raise TypeError(
                    f"content must either be a list or callable, got {type(content)=}"
                )

            action = self.derive_button_action_from_content(content, *options)
            btn = update_button(action, "")

            text = TextureText.create(
                text=label, start_x=0, lines=1, font_name=WindowData.font, font_size=27
            )
            self.sprite_list.append(text.sprite)

            btn.size_hint = (1, None)
            btn.resize(height=50)
            btn.style = self.button_style
            self.main_box.add(btn)

        self.position_labels()

    def position_labels(self):
        incr = 0
        for sprite in self.sprite_list:
            sprite.center_x, sprite.center_y = (
                self.anchor.center_x,
                (self.anchor.top - 20) - incr,
            )
            incr += 52

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
