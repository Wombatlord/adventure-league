from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import arcade
from arcade.gui import Rect
from pyglet.math import Vec2

from src import config
from src.engine.init_engine import eng
from src.gui.combat.combat_log import CombatLog
from src.gui.combat.combat_menu import CombatMenu, empty
from src.gui.combat.portrait import Pin, Portrait
from src.utils.rectangle import Rectangle

if TYPE_CHECKING:
    from src.gui.combat.scene import Scene

from src.world.node import Node


def _subdivision(axis_split: int, size: tuple[int, int], tile: tuple[int, int]) -> Rect:
    region = Vec2(*size) / axis_split
    return Rect(tile[0] * region.x, tile[1] * region.y, *region)


class HUD(arcade.Section):
    scene: Scene
    combat_menu: CombatMenu
    dispatch_mouse: Callable[[int, int, int, int], Node | None]

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
        self.dispatch_mouse = lambda *_: None
        self.debug_text = arcade.Text(
            text="",
            font_size=12,
            start_x=10,
            start_y=self.height - 10,
            multiline=True,
            width=self.width // 2,
        )
        self.hud_camera = arcade.Camera()
        portrait_height, portrait_width = 200, 200

        self.setup_player_portrait(portrait_height, portrait_width)
        self.setup_hover_portrait(portrait_height, portrait_width)
        self.allow_dispatch_mouse()

        eng.subscribe(
            topic="await_input",
            handler_id="combat.hud.handle_input_request",
            handler=self.handle_input_request,
        )
        eng.subscribe(
            topic="turn_end",
            handler_id="Portrait.clear.player",
            handler=self.player_character_portrait.clear,
        )
        self.health_bars_visible = False

    def setup_hover_portrait(self, portrait_height, portrait_width):
        bl_margins = Vec2(50, 0)
        self.hover_portrait = Portrait(
            Rectangle.from_lbwh((0, 0, portrait_width, portrait_height)).translate(
                bl_margins
            ),
            flip=False,
        )
        enemy_portrait_pinned_pt = lambda: self.hover_portrait.rect.corners[0]
        bl_pin = Pin(self.get_anchor_bottom_left(bl_margins), enemy_portrait_pinned_pt)
        self.hover_portrait.pin_rect(bl_pin)

    def setup_player_portrait(self, portrait_height, portrait_width):
        window_l_to_r = Vec2(*(arcade.get_window().size[0], 0))
        br_margins = Vec2(-50, 0)
        self.player_character_portrait = Portrait(
            Rectangle.from_lbwh((0, 0, portrait_width, portrait_height)).translate(
                window_l_to_r + br_margins - Vec2(portrait_width, 0)
            )
        )
        player_char_pinned_pt = lambda: self.player_character_portrait.rect.corners[3]
        br_pin = Pin(self.get_anchor_bottom_right(br_margins), player_char_pinned_pt)
        self.player_character_portrait.pin_rect(br_pin)

    def get_anchor_bottom_right(self, margin: Vec2) -> Callable[[], Vec2]:
        return lambda: Vec2(arcade.get_window().size[0], 0) + margin

    def get_anchor_bottom_left(self, margin: Vec2) -> Callable[[], Vec2]:
        return lambda: margin

    def enter_move_selection(self):
        self.allow_dispatch_mouse()
        self.combat_menu.menu.hide()

    def leave_move_selection(self):
        self.prevent_dispatch_mouse()
        self.combat_menu.menu.enable()
        self.combat_menu.menu.show()

    def allow_dispatch_mouse(self):
        self.dispatch_mouse = self.scene.update_mouse_node

    def prevent_dispatch_mouse(self):
        self.dispatch_mouse = lambda *_: None

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        node = self.dispatch_mouse(x, y, dx, dy)
        if node is None:
            return

        if hovered := self.scene.entity_at_node(node):
            self.hover_portrait.set_sprite(hovered.entity_sprite.sprite)
        else:
            self.hover_portrait.clear()

        if self.combat_menu.is_selecting_move():
            self.combat_menu.move_selection.on_selection_changed()

        elif self.combat_menu.is_selecting_spell_target():
            self.combat_menu.menu.current_node_selection.on_selection_changed()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.combat_menu.is_selecting_move():
            self.combat_menu.move_selection.on_selection_confirmed()

        elif self.combat_menu.is_selecting_spell_target():
            self.combat_menu.menu.current_node_selection.on_selection_confirmed()

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
        self.player_character_portrait.set_sprite(requester.owner.entity_sprite.sprite)

        menu_rect = self.get_menu_rect(250, 250)
        self.combat_menu = (
            CombatMenu(scene=self.scene, hud=self)
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
        self.combat_menu.menu.enable()

    def clear_menu(self):
        self.combat_menu.menu.disable()
        self.combat_menu.move_selection.disable()
        self.combat_menu = empty()
        self.player_character_portrait.clear()
        eng.input_received()

    def on_draw(self):
        self.hud_camera.use()
        self.combat_log.draw()
        self.combat_menu.menu.draw()
        self.player_character_portrait.draw()
        self.hover_portrait.draw()
        if not config.DEBUG:
            return
        self.debug_text.draw()

    def on_update(self, delta_time: float):
        self.player_character_portrait.update()
        self.hover_portrait.update()
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
        self.player_character_portrait.on_resize()
        self.hover_portrait.on_resize()

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.P:
                breakpoint()

            case arcade.key.ESCAPE:
                self.combat_menu.move_selection.disable()
            case arcade.key.H:
                self.health_bars_visible = (
                    self.scene.floating_health_bars.toggle_visible()
                )
            case _:
                pass
