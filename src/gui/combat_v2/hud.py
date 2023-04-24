from __future__ import annotations

from typing import TYPE_CHECKING

import arcade
from arcade.gui import Rect
from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.gui.combat_v2 import combat_menu
from src.gui.combat_v2.combat_log import CombatLog
from src.gui.combat_v2.types import Highlighter

if TYPE_CHECKING:
    from src.gui.combat_v2.scene import Scene


def _subdivision(axis_split: int, size: tuple[int, int], tile: tuple[int, int]) -> Rect:
    region = Vec2(*size) / axis_split
    return Rect(tile[0] * region.x, tile[1] * region.y, *region)


class HUD(arcade.Section):
    def __init__(
        self,
        scene: Scene,
    ):
        super().__init__(
            scene.left,
            scene.bottom,
            scene.width,
            scene.height,
            prevent_dispatch={False},
            draw_order=100,
        )
        self.scene = scene
        self.combat_log = CombatLog(_subdivision(3, (self.width, self.height), (2, 2)))
        self.combat_menu = combat_menu.empty()

        eng.subscribe(
            topic="await_input",
            handler_id="combat.hud.handle_input_request",
            handler=self.handle_input_request,
        )

    def handle_input_request(self, event):
        eng.await_input()
        self.combat_menu = combat_menu.from_event(
            event,
            get_current_node=self.scene.get_mouse_node,
            on_teardown=self.clear_menu,
            highlighter=Highlighter(
                clear=self.scene.clear_highlight, highlight=self.scene.show_highlight
            ),
        )

    def enable_combat_menu(self):
        self.combat_menu.enable()

    def clear_menu(self):
        self.combat_menu = combat_menu.empty()

    def on_draw(self):
        self.combat_log.draw()

    def on_update(self, delta_time: float):
        self.combat_log.on_update()
