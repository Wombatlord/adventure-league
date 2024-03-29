from typing import Callable

import arcade
from arcade.gui import UIManager

from src.engine.init_engine import eng
from src.gui.combat.action_report import ActionReport
from src.gui.combat.hud import HUD
from src.gui.combat.scene import Scene


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
        self.action_report = ActionReport(
            left=window_dims[0] * 0.25,
            bottom=window_dims[1] * 0.25,
            width=window_dims[0] - window_dims[0] * 0.25,
            height=window_dims[1] - window_dims[1] * 0.25,
        )
        self.add_section(self.hud)
        self.add_section(self.scene)
        self.add_section(self.action_report)
        eng.init_combat()

    def on_draw(self):
        self.clear()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.hud.on_resize(width, height)
