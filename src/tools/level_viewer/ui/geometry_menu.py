from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import arcade
from arcade import gui
from arcade.gui import UIManager

from src.tools.level_viewer.ui.hides import Hides

if TYPE_CHECKING:
    from src.tools.level_viewer.ui.layout import LayoutSection

from src.tools.level_viewer.model.layout import Block, _viewable_layouts
from src.world.level.room_layouts import Terrain
from src.world.node import Node

NO_OP = lambda *_, **__: None
BlockFactory = Callable[[], list[Block]]


class GeometryMenu(arcade.Section, Hides):
    layout: LayoutSection
    dispatch_mouse: Callable[[int, int, int, int], Node | None]

    def __init__(
        self,
        layout: LayoutSection,
    ):
        super().__init__(
            layout.left,
            layout.bottom,
            layout.width,
            layout.height,
            prevent_dispatch={True},
            prevent_dispatch_view={False},
            draw_order=100,
        )
        self.layout = layout
        self.ui_manager = UIManager()

        self.setup_ui()

    def factory_button(
        self, name: str, factories: BlockFactory, height_hint: float
    ) -> gui.UIFlatButton:
        btn = gui.UIFlatButton(text=name, size_hint=(1, height_hint))
        layout = factories
        btn.on_click = lambda *_: self.layout.show_layout(layout())
        return btn

    def setup_ui(self):
        self.ui_manager.add(
            gui.UIBoxLayout(
                x=0,
                y=0,
                width=self.width / 5,
                height=self.height,
                children=[
                    self.factory_button(name, factory, 1 / len(_viewable_layouts))
                    for name, factory in _viewable_layouts.items()
                ],
            )
        )

    def on_update(self, delta_time: float):
        self.ui_manager.on_update(delta_time)

    def on_draw(self):
        self.ui_manager.draw()

    def on_hide(self):
        self.prevent_dispatch = {False}
        self.ui_manager.disable()

    def on_show(self):
        self.prevent_dispatch = {True}
        self.ui_manager.enable()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.ui_manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.ui_manager.on_mouse_release(x, y, button, modifiers)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.ui_manager.on_mouse_motion(x, y, dx, dy)

    def bp(self):
        breakpoint()

    def on_key_press(self, symbol: int, modifiers: int):
        {arcade.key.P: self.bp}.get(symbol, NO_OP)()
