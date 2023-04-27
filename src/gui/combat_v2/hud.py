from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable

import arcade
from arcade.gui import Rect
from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.entities.sprites import BaseSprite
from src.gui.combat_v2.combat_log import CombatLog
from src.gui.combat_v2.combat_menu import CombatMenu, empty
from src.utils.rectangle import Rectangle

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
            width=self.width // 2,
        )
        self.hud_camera = arcade.Camera()
        portrait_height, portrait_width = 150, 200

        self.setup_player_portrait(portrait_height, portrait_width)
        self.setup_enemy_portrait(portrait_height, portrait_width)

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
        eng.subscribe(
            topic="turn_end",
            handler_id="Portrait.clear.enemy",
            handler=self.enemy_portrait.clear,
        )

    def setup_enemy_portrait(self, portrait_height, portrait_width):
        bl_margins = Vec2(50, 0)
        self.enemy_portrait = Portrait(
            Rectangle.from_lbwh((0, 0, portrait_width, portrait_height)).translate(
                bl_margins
            ),
            flip=False,
        )
        enemy_portrait_pinned_pt = lambda: self.enemy_portrait.rect.corners[0]
        bl_pin = Pin(self.get_anchor_bottom_left(bl_margins), enemy_portrait_pinned_pt)
        self.enemy_portrait.pin_rect(bl_pin)

    def setup_player_portrait(self, portrait_width, portrait_height):
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
                self.enemy_portrait.set_sprite(requester.owner.entity_sprite.sprite)
                return

        eng.await_input()
        self.player_character_portrait.set_sprite(requester.owner.entity_sprite.sprite)

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
        self.debug_text.draw()
        self.player_character_portrait.draw()
        self.enemy_portrait.draw()

    def on_update(self, delta_time: float):
        self.combat_log.on_update()
        self.player_character_portrait.update()
        self.enemy_portrait.update()
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
        self.enemy_portrait.on_resize()

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.ESCAPE:
                self.combat_menu.move_selection.disable()
            case _:
                pass


class Pin:
    def __init__(self, get_pin: Callable[[], Vec2], get_pinned_pt: Callable[[], Vec2]):
        self.get_pin = get_pin
        self.get_pinned_pt = get_pinned_pt

    def get_translation(self) -> Vec2:
        return self.get_pin() - self.get_pinned_pt()


class Portrait:
    TEXT_SLOT_HEIGHT = 50

    _base_sprite: BaseSprite | None
    _base_texture: arcade.Texture | None
    _rect: Rectangle
    _translate: Vec2
    _pin: Pin | None
    _flip: bool

    sprite: arcade.Sprite | None
    pictured: Entity | None

    def __init__(self, rect: Rectangle, flip: bool = True):
        self._should_update = False
        self._base_sprite = None
        self._base_texture = None
        self._sprites = arcade.SpriteList()
        self._translate = Vec2()
        self._flip = flip

        self.sprite = None
        self.rect = rect
        self.pictured = None

        top_text_start = self.text_start_above()
        self._top_text = arcade.Text(
            text="", start_x=top_text_start.x, start_y=top_text_start.y, font_size=18
        )
        btm_text_start = self.text_start_below()
        self._bottom_text = arcade.Text(
            text="", start_x=btm_text_start.x, start_y=btm_text_start.y, font_size=18
        )

    def _check_base_tex(self) -> arcade.Texture | None:
        if self._base_sprite:
            return self._base_sprite.texture

        return None

    def pin_rect(self, pin: Pin):
        self._pin = pin

    @property
    def rect(self) -> Rectangle:
        return self._rect

    def get_rect(self) -> Rectangle:
        return self._rect

    @rect.setter
    def rect(self, value: Rectangle):
        if not isinstance(value, Rectangle):
            raise TypeError(f"expected a value of type {Rectangle}, got {value}")
        window_size = arcade.get_window().size
        window_rect = Rectangle(0, window_size[0], 0, window_size[1])
        if value not in window_rect:
            msg = f"rectangle {value} out of window bounds {window_rect}"
            raise ValueError(msg)

        *_, br = value.corners
        self._rect = value

    def on_resize(self):
        if self._pin:
            self._translate = self._pin.get_translation()
        print(self._translate)
        self.update(force=True)

    @property
    def name_start(self):
        return self.text_start_above()

    @property
    def size(self) -> Vec2:
        return self._rect.dims

    def set_sprite(self, sprite: BaseSprite | None):
        self._sprites.clear()

        if sprite is None:
            self.clear()
            return

        self.pictured = sprite.owner.owner
        self._base_texture = sprite.texture
        self._base_sprite = sprite

        self.update(force=True)
        self._sprites.append(self.sprite)

    def clear(self, _=None):
        self.sprite = None
        self._base_sprite = None
        self._base_texture = None
        self.pictured = None
        self._top_text.text = ""
        self._bottom_text.text = ""
        self._sprites.clear()
        self.update(force=True)

    @property
    def should_update(self) -> bool:
        texture_changed = (
            self._base_sprite and self._base_sprite.texture != self._base_texture
        )

        return self._should_update or texture_changed

    def update(self, force=False):
        self.rect = self.rect.translate(self._translate)
        self.update_top()
        self.update_btm()
        if self.should_update or force:
            self.update_sprite()
            self._should_update = False
        self._translate = Vec2()

    @property
    def bottom_right(self) -> Vec2:
        return Vec2(self.rect.r, self.rect.b)

    def sprite_scale(self, cropped: arcade.Texture) -> float:
        scale = self.sprite_slot.h / cropped.height
        return scale

    def update_sprite(self):
        print("update sprite called")
        if self._base_sprite is None:
            return

        # store the texture we intend to crop
        self._base_texture = self._base_sprite.texture

        # do the crop
        src = self._base_sprite.texture

        # pillow style (whoopsie!)
        cropped = src.crop(0, 0, src.width, src.height // 2 + 2)
        if self._flip:
            cropped = cropped.flip_left_right()

        if self.sprite is not None:
            # if we have a sprite just update the texture
            self.sprite.texture = cropped
        else:
            # otherwise, set the sprite
            self.sprite = arcade.Sprite(cropped, scale=self.sprite_scale(cropped))

        # Position the sprite
        self.sprite.center_x = self.sprite_slot.center.x
        self.sprite.center_y = self.sprite_slot.center.y

    def update_top(self):
        self._top_text.position = (
            self.top_slot.center - Vec2(self._top_text.content_width, 0) / 2
        )
        if self.pictured is not None:
            self._top_text.text = f"{self.pictured.name}"
        else:
            self._top_text.text = ""

    def update_btm(self):
        self._bottom_text.position = (
            self.bottom_slot.center - Vec2(self._bottom_text.content_width, 0) / 2
        )
        if self.pictured is not None:
            current = self.pictured.fighter.health.current
            max_h = self.pictured.fighter.health.max_hp
            missing = max_h - current
            self._bottom_text.text = (
                f"HP: {self.pictured.fighter.health.current} "
                + "-" * round(10 * missing / max_h)
                + "#" * round(10 * current / max_h)
            )
        else:
            self._bottom_text.text = ""

    def draw(self):
        self._sprites.draw(pixelated=True)
        self._bottom_text.draw()
        self._top_text.draw()

    @property
    def top_slot(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=Vec2(self._rect.l, self._rect.t - self.TEXT_SLOT_HEIGHT),
            max_v=self._rect.max,
        )

    @property
    def sprite_slot(self) -> Rectangle:
        *_, max_v, _ = self.top_slot.corners
        _, min_v, *_ = self.bottom_slot.corners
        return Rectangle.from_limits(min_v, max_v)

    @property
    def bottom_slot(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=self._rect.min,
            max_v=Vec2(self._rect.r, self._rect.b + self.TEXT_SLOT_HEIGHT),
        )

    def text_start_below(self) -> Vec2:
        return self.bottom_slot.min + Vec2(0, self.bottom_slot.h) / 2

    def text_start_above(self) -> Vec2:
        return self.top_slot.min + Vec2(0, self.top_slot.h) / 2
