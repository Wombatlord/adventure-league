from __future__ import annotations

from typing import Callable

import arcade
from pyglet.math import Vec2

from src import config
from src.entities.entity import Entity
from src.entities.sprites import BaseSprite
from src.gui.combat.health_bar import HealthBar
from src.utils.rectangle import Rectangle


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
        self._health_bar = HealthBar(scale=4)

        top_text_start = self.text_start_above()
        self._top_text = arcade.Text(
            text="",
            start_x=top_text_start.x,
            start_y=top_text_start.y,
            font_size=16,
            anchor_x="center",
        )
        btm_text_start = self.text_start_below()
        self._bottom_text = arcade.Text(
            text="",
            start_x=btm_text_start.x,
            start_y=btm_text_start.y,
            font_size=10,
            anchor_y="center",
            anchor_x="right",
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

        if self.pictured is not sprite.owner.owner:
            self.pictured = sprite.owner.owner
            self._health_bar.set_watched_health(self.pictured.fighter.health)

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
        self._health_bar.set_watched_health(None)
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
        if self._base_sprite is None:
            return

        # store the texture we intend to crop
        self._base_texture = self._base_sprite.texture

        # do the crop
        src = self._base_sprite.texture

        # hitbox height
        ys = [pt[1] for pt in src.hit_box_points]
        height = int(max(ys) - min(ys))
        empty_px_above = src.height - height

        # pillow style cropping with increasing y from top to btm (whoopsie!)
        # the crop_start_y allows sprites when most of the top of the sprite is empty to
        # effectively move up in the frame so they aren't completely cut off
        crop_start_y = max(empty_px_above - 2, 0)
        cropped = src.crop(0, crop_start_y, src.width, 8)
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
        self._top_text.position = self.text_start_above()
        if self.pictured is not None:
            self._top_text.text = f"{self.pictured.name.name_and_title}"
        else:
            self._top_text.text = ""

    def update_btm(self):
        self._bottom_text.position = self.text_start_below()

        # self._health_bar.v_align(self.bottom_slot.center.y)
        self._health_bar.update()
        if self.pictured is not None:
            current = self.pictured.fighter.health.current
            max_h = self.pictured.fighter.health.max_hp
            self._bottom_text.text = f"HP: {current}/{max_h}"
        else:
            self._bottom_text.text = ""
        health_bar_pos = self.bottom_slot.lerp(
            Vec2(0.5, 0.5) + Vec2(1 / 6, 0), translate=True
        )
        self._health_bar.set_position(health_bar_pos)

    def draw(self):
        self._sprites.draw(pixelated=True)
        self._bottom_text.draw()
        self._top_text.draw()
        self._health_bar.draw()
        if not config.DEBUG:
            return

        for c in self.rect.corners:
            arcade.draw_point(c.x, c.y, arcade.color.RED, 5)

        for sprite in self._sprites:
            sprite.draw_hit_box(color=arcade.color.BLUE, line_thickness=1)

    @property
    def top_slot(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=Vec2(self._rect.l, self._rect.t - self.TEXT_SLOT_HEIGHT),
            max_v=self._rect.max,
        )

    @property
    def sprite_slot(self) -> Rectangle:
        *_, max_v = self.top_slot.corners
        _, min_v, *_ = self.bottom_slot.corners
        return Rectangle.from_limits(min_v, max_v)

    @property
    def bottom_slot(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=self._rect.min,
            max_v=Vec2(self._rect.r, self._rect.b + self.TEXT_SLOT_HEIGHT),
        )

    def text_start_below(self) -> Vec2:
        return Vec2(*self._health_bar.sprite.position) + Vec2(
            -(self._health_bar.sprite.width / 2 + 4), 3
        )

    def text_start_above(self) -> Vec2:
        return self.top_slot.lerp(Vec2(0.5, 0.6), translate=True)
