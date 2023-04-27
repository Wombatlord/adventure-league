from __future__ import annotations

import math

import arcade
from pyglet.math import Vec2

from src.entities.combat.stats import HealthPool
from src.textures.texture_data import SingleTextureSpecs


class HealthBar:
    _full_bar: arcade.Texture
    BAR_INCREMENTS = 32
    _watched_health: HealthPool | None
    _state: tuple[int, int]
    _do_update: bool
    _position: Vec2
    _scale: float

    def __init__(self, scale: float):
        self._scale = scale
        self._full_bar = SingleTextureSpecs.health_bar.loaded
        self.sprite_list = arcade.SpriteList()
        self._state = 1, 1
        self._watched_health = None
        self._do_update = False
        self._position = Vec2()
        self._update_sprite()
        self.hide()

    def _update_sprite(self):
        self.sprite = arcade.Sprite(self._get_crop(*self._state), scale=self._scale)
        self.sprite_list.clear()
        self.sprite_list.append(self.sprite)
        self.sprite.position = self._position

    def _get_crop(self, current: int, max_hp: int) -> arcade.Texture:
        bar = self._full_bar
        offset = -round(math.floor((self.BAR_INCREMENTS * current) / max_hp))
        crop_start_x = self.BAR_INCREMENTS + offset
        return bar.crop(crop_start_x, 0, self.BAR_INCREMENTS, bar.height)

    def set_watched_health(self, health: HealthPool | None):
        self._watched_health = health
        if self._watched_health is not None:
            self.show()
        self._check_state()

    def _derive_state(self) -> tuple[int, int]:
        if self._watched_health is None:
            return (1, 1)
        else:
            return (self._watched_health.current, self._watched_health.max_hp)

    def _check_state(self):
        if (new_state := self._derive_state()) != self._state:
            self._state = new_state
            self._do_update = True

        if (new_position := self._position) != Vec2(*self.sprite.position):
            self.sprite.position = new_position
            self._do_update = True

    def hide(self):
        self.sprite.visible = False

    def show(self):
        self.sprite.visible = True

    def move_by(self, translation: Vec2):
        self._position += translation
        self._check_state()

    def set_position(self, position: Vec2):
        self._position = position
        self._check_state()

    def h_align(self, center: float):
        self._position = Vec2(self._position.x, center)
        self._check_state()

    def v_align(self, center: float):
        self._position = Vec2(center, self._position.y)
        self._check_state()

    def update(self):
        self._check_state()
        if not self._do_update:
            return

        self._update_sprite()

        if self._watched_health is None:
            self.hide()
        else:
            self.show()

    def draw(self):
        self.sprite_list.draw(pixelated=True)
