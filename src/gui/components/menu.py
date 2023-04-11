from arcade.gui import UIFlatButton, UIEvent, UIManager, UIBoxLayout
from typing import Self, Callable, NamedTuple
from types import FunctionType
# DATA STRUCTURES
ExecutableMenuItem = tuple[str, Callable[[UIEvent], None]]


class MenuNode(NamedTuple):
    label: str
    content: ExecutableMenuItem | list[Self]

SubMenu = list[ExecutableMenuItem]
MenuWithSubMenu = tuple[str, SubMenu]
MenuSchema = list[MenuWithSubMenu | ExecutableMenuItem]



# LE MENU
from src.gui.components.buttons import update_button
class Menu:
    def __init__(self, menu_config: MenuSchema, pos: tuple[int, int], area: tuple[int,int]) -> None:
        self.full_menu_graph = menu_config
        self.manager = UIManager()
        self.x, self.y = pos
        self.width, self.height = area
        self.main_box = UIBoxLayout(x=self.x, y=self.y, width=self.width, height=self.height)
        self.manager.add(self.main_box)
    
    def build_menu(self, menu: MenuSchema):
        self.main_box.clear()
        
        for label, content in menu:
            action = self.derive_button_action_from_content(content)
            btn = update_button(on_click=action, text=label)
            self.main_box.add(btn)


    def derive_button_action_from_content(self, content: Callable[[UIEvent], None] | list) -> Callable[[UIEvent], None]:
        action = None
        match content:
            case func if isinstance(func, Callable | FunctionType):
                action = func
                
            case sub_menu if isinstance(sub_menu, list | tuple):
                action = self.open_sub_menu_action(sub_menu=sub_menu)
            
            case _:
                raise TypeError(f"{content} should be Callable or SubMenu, got {type(content)=}")

        return action


    def open_sub_menu_action(self, sub_menu) -> Callable[[UIEvent], None]:
        def _on_click() -> None:
            self.enter_submenu(sub_menu)

        return _on_click
        
    def enter_submenu(self, menu:MenuSchema):
        self.build_menu(menu)
        self.add_return_to_top_level_button()

    def add_return_to_top_level_button(self):
        btn = UIFlatButton(text="return")
        btn.on_click = lambda _: self.build_menu(self.full_menu_graph)
        self.main_box.add(btn)
