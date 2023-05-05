from __future__ import annotations

import math
from typing import Sequence

import arcade
from pyglet.math import Vec2

from src.entities.combat.fighter import Fighter
from src.entities.combat.stats import HealthPool
from src.entities.sprites import BaseSprite
from src.textures.texture_data import SingleTextureSpecs
from src.world.isometry.transforms import Transform


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
        self.sprite = None
        self._position = Vec2()
        self._update_sprite()
        self.hide()

    def _update_sprite(self):
        if not self.sprite:
            self.sprite = arcade.Sprite(self._get_crop(*self._state), scale=self._scale)
        else:
            self.sprite.texture = self._get_crop(*self._state)
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


class FloatingHealthBar:
    _health_bar: HealthBar
    _fighter: Fighter
    _sprite: BaseSprite
    _world_sprites: arcade.SpriteList

    def __init__(
        self, fighter: Fighter, world_sprites: arcade.SpriteList, transform: Transform
    ):
        self._fighter = fighter
        self._health_bar = HealthBar(fighter.owner.entity_sprite.sprite.scale / 2)
        self._health_bar.set_watched_health(self._fighter.health)
        self._world_sprites = world_sprites

        self._sprite = (
            BaseSprite(
                self._health_bar.sprite.texture,
                scale=self._health_bar.sprite.scale,
            )
            .offset_anchor((0, 16))
            .set_transform(transform)
            .set_node(self._fighter.location)
        )

        self._world_sprites.append(self._sprite)

    def update(self):
        if self._fighter.incapacitated:
            self._sprite.visible = False

            if self._sprite in self._world_sprites:
                self._world_sprites.remove(self._sprite)
            return

        self._health_bar.update()
        self._sprite.texture = self._health_bar.sprite.texture
        self._sprite.set_node(self._fighter.location)

    @property
    def should_delete(self) -> bool:
        return self._fighter.incapacitated

    @property
    def attached_fighter(self) -> Fighter:
        return self._fighter

    def show(self):
        self._sprite.visible = True

    def hide(self):
        self._sprite.visible = False


class FloatingHealthBars:
    _health_bars: list[FloatingHealthBar]
    _attached_fighters: list[Fighter]
    _world_sprites: arcade.SpriteList
    _transform: Transform

    def __init__(self, world_sprites: arcade.SpriteList, transform: Transform):
        self._health_bars = []
        self._world_sprites = world_sprites
        self._transform = transform
        self._attached_fighters = []
        self._hidden = True

    def attach(self, fighter: Fighter):
        if fighter in self._attached_fighters:
            return
        self._attached_fighters.append(fighter)
        floating_bar = FloatingHealthBar(fighter, self._world_sprites, self._transform)
        if self.hidden:
            floating_bar.hide()
        self._health_bars.append(floating_bar)

    def attach_all(self, fighters: Sequence[Fighter]):
        for fighter in fighters:
            self.attach(fighter)

    def flush(self):
        self._attached_fighters = []
        self._health_bars = []

    def update(self):
        for health_bar in self._health_bars:
            health_bar.update()
            if health_bar.should_delete:
                self._attached_fighters.remove(health_bar.attached_fighter)
                self._health_bars.remove(health_bar)

    def show(self):
        self._hidden = False
        for bar in self._health_bars:
            bar.show()

    def hide(self):
        self._hidden = True
        for bar in self._health_bars:
            bar.hide()

    @property
    def hidden(self) -> bool:
        return self._hidden

    def visible(self) -> bool:
        return not self._hidden

    def toggle_visible(self):
        if self._hidden:
            self.show()
        else:
            self.hide()

        return not self._hidden
