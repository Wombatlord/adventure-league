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
    manager: UIManager

    def __init__(
        self,
        menu_config: MenuSchema,
        pos: tuple[int, int],
        area: tuple[int, int],
        button_style: UIStyle | None = None,
    ) -> None:
        self.full_menu_graph = menu_config
        self.current_menu_graph = menu_config
        self.x, self.y = pos
        self.width, self.height = area
        self.manager = None
        self.main_box = None
        self.button_style = button_style or ADVENTURE_STYLE
        self.button_size = 50
        self.sprite_list = arcade.SpriteList()
        self._setup()

        """
        Added a sprite list for internally handling TextureText objects.
        Currently the labels are positioned via magic numbers and sort of correctly overlap the initial MainMenu layout.
        
        Problems:
        The manager grows vertically upwards rather than downward if there are more buttons in the submenu than parent.
        
        TextureText positioning isn't properly tied to a button position.
        
        A menu build doesn't correctly position labels for submenus
        
        The possible existence of a Return button isn't accounted for in a build_menu call, it's just stuck on after.
        This prevents neat use of size properties of main_box for label positioning.
        
        Button.center_x/y do not correspond to their position on screen. Checking the values in the debugger says they're at 25ish
        the main_box positioning is what actually puts them where they appear, so aligning the TextureText to the button isn't 
        just a case of setting those to equal.
        """

    def _setup(self):
        if self.manager:
            self.manager.clear()
        else:
            self.manager = UIManager()

        self.anchor = UIAnchorLayout(width=self.width, height=self.height)

        self.main_box = UIBoxLayout(
            width=self.width,
            height=self.height,
            size_hint=(None, None),
            space_between=2,
        ).with_border(color=arcade.color.RED)

        self.anchor.add(self.main_box, anchor_x="center", anchor_y="center")
        self.manager.add(self.anchor)
        self.build_menu(self.current_menu_graph)

    def disable(self):
        self.manager.disable()
        self.manager.clear()

    def enable(self):
        self._setup()
        self.manager.enable()
        self.draw()

    def draw(self):
        if self.manager._enabled:
            self.manager.draw()
            self.sprite_list.draw(pixelated=True)

    def is_enabled(self) -> bool:
        return self.manager._enabled

    def build_menu(self, menu: MenuSchema):
        self.main_box.clear()
        self.main_box.resize(
            width=self.width, height=self.button_size * len(menu)
        )  # Ensure the height of main box is some multiple of the button size (50)
        self.sprite_list.clear()
        texture_text_y_incrementer = 50
        for label, content, *options in menu:
            if not isinstance(label, str):
                raise TypeError(f"label must be a string, got {type(label)=}")
            if not callable(content) and not isinstance(content, list):
                raise TypeError(
                    f"content must either be a list or callable, got {type(content)=}"
                )

            action = self.derive_button_action_from_content(content, *options)
            btn = update_button(action, "")
            btn.size_hint = (1, None)
            btn.resize(height=self.button_size)
            btn.style = self.button_style

            text = TextureText(
                text=label,
                start_x=0,
                lines=1,
                color=arcade.color.WHITE,
                font_size=12,
                width=self.width,
                font_name=WindowData.font,
                multiline=True,
                anchor_y="baseline",
            )

            # This is cursed
            text.center_x = self.x

            text.center_y = ((self.y + self.height) + 5) - texture_text_y_incrementer
            texture_text_y_incrementer += 52
            # breakpoint()
            text.scale = 3
            self.sprite_list.append(text.sprite)
            self.main_box.add(btn)

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
        self.add_return_to_top_level_button()

    def add_return_to_top_level_button(self):
        btn = update_button(
            on_click=lambda: self.build_menu(self.full_menu_graph), text="Return"
        )
        btn.resize(height=50)
        btn.style = ADVENTURE_STYLE
        btn.size_hint = (1, None)
        self.main_box.add(btn)
