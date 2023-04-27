from __future__ import annotations

from typing import Callable

import arcade
from pyglet.math import Vec2

from src.entities.entity import Entity
from src.entities.sprites import BaseSprite
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
