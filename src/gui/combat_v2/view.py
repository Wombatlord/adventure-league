from typing import Callable

import arcade
from arcade.gui import UIManager

from src.engine.init_engine import eng
from src.gui.combat_v2.hud import HUD
from src.gui.combat_v2.scene import Scene


class CombatView(arcade.View):
    def __init__(self, parent_factory: Callable[[], arcade.View]):
        super().__init__()
        window_dims = arcade.get_window().size
        self.parent_factory = parent_factory
        self.manager = UIManager()
        self.scene = Scene(
            left=0, bottom=0, width=window_dims[0], height=window_dims[1]
        )
        self.hud = HUD(scene=self.scene)

        self.add_section(self.hud)
        self.add_section(self.scene)
        eng.init_combat()

    def on_draw(self):
        self.clear()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.hud.on_resize(width, height)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    self.window.show_view(self.parent_factory())
