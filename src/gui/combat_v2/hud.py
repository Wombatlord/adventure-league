from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Callable

import arcade
from arcade.gui import Rect
from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.gui.animation.positioning import maintain_position
from src.gui.combat_v2.combat_log import CombatLog
from src.gui.combat_v2.combat_menu import CombatMenu, empty, from_event
from src.gui.combat_v2.types import Highlighter
from src.utils.rectangle import Rectangle
from src.world.node import Node

if TYPE_CHECKING:
    from src.gui.combat_v2.scene import Scene


def _subdivision(axis_split: int, size: tuple[int, int], tile: tuple[int, int]) -> Rect:
    region = Vec2(*size) / axis_split
    return Rect(tile[0] * region.x, tile[1] * region.y, *region)


class HUD(arcade.Section):
    scene: Scene
    combat_menu: CombatMenu

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
            prevent_dispatch_view={False},
            draw_order=100,
        )
        self.scene = scene
        self.combat_log = CombatLog(_subdivision(3, (self.width, self.height), (2, 2)))
        self.combat_menu = empty()
        self.dispatch_mouse = lambda *_: False
        self.debug_text = arcade.Text(
            text="",
            font_size=12,
            start_x=10,
            start_y=self.height - 10,
            multiline=True,
            width=self.width / 2,
        )
        self.hud_camera = arcade.Camera()

        eng.subscribe(
            topic="await_input",
            handler_id="combat.hud.handle_input_request",
            handler=self.handle_input_request,
        )

    def enter_move_selection(self):
        self.allow_dispatch_mouse()
        self.combat_menu.menu.hide()

    def leave_move_selection(self):
        self.prevent_dispatch_mouse(self)
        self.combat_menu.enable()
        self.combat_menu.show()

    def allow_dispatch_mouse(self):
        self.dispatch_mouse = self.scene.update_mouse_node

    def prevent_dispatch_mouse(self):
        self.dispatch_mouse = lambda *_: False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        node = self.dispatch_mouse(x, y, dx, dy)
        if node and self.combat_menu.is_selecting_move():
            self.combat_menu.move_selection.on_selection_changed()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.combat_menu.is_selecting_move():
            self.combat_menu.move_selection.on_selection_confirmed()

    def get_menu_rect(self, menu_w: float, menu_h: float) -> Rectangle:
        return Rectangle.from_xywh(
            x=0,
            y=0,
            w=menu_w,
            h=menu_h,
        ).translate(
            Vec2(self.width - menu_w * 0.51, self.height * (2 / 3) - menu_h * 0.51)
        )

    def handle_input_request(self, event):
        if requester := event.get("await_input"):
            self.scene.follow(requester.locatable)
            if requester.owner.ai:
                return

        eng.await_input()

        menu_rect = self.get_menu_rect(250, 250)
        self.combat_menu = (
            CombatMenu(
                scene=self.scene,
            )
            .set_on_teardown(self.clear_menu)
            .set_highlight(self.scene.show_highlight)
            .set_menu_rect(menu_rect)
            .build(event)
        )

        move_selection = self.combat_menu.move_selection
        move_selection.set_on_enter(self.enter_move_selection)
        move_selection.set_clear_templates(self.scene.clear_highlight)

        move_selection.set_enable_parent_menu(self.leave_move_selection)

        self.combat_menu.menu.enable()
        self.combat_menu.menu.show()

    def enable_combat_menu(self):
        self.combat_menu.enable()

    def clear_menu(self):
        self.combat_menu.menu.disable()
        self.combat_menu.move_selection.disable()
        self.combat_menu = empty()
        eng.input_received()

    def on_draw(self):
        self.hud_camera.use()
        self.combat_log.draw()
        self.combat_menu.menu.draw()
        self.debug_text.draw()

    def on_update(self, delta_time: float):
        self.combat_log.on_update()
        if self.combat_menu.menu.is_enabled():
            self.combat_menu.menu.update()

        self.debug_text.text = (
            f"{self.dispatch_mouse=}\n"
            f"{self.scene.last_mouse_node=}\n"
            f"{self.scene._mouse_coords=}\n"
            f"{self.combat_menu.menu.x=}\n"
            f"{self.width=}, {self.height=}\n"
        )

    def on_resize(self, width: int, height: int):
        self.width, self.height = width, height
        self.hud_camera.resize(width, height)
        self.combat_menu.set_menu_rect(self.get_menu_rect(250, 250))
        self.combat_log.on_resize(width, height)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.ESCAPE:
                self.combat_menu.move_selection.disable()
            case _:
                pass
