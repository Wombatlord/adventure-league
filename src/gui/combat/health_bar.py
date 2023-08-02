from __future__ import annotations

import math
from functools import lru_cache
from typing import Sequence

import arcade
from pyglet.math import Vec2

from src.entities.combat.fighter import Fighter
from src.entities.combat.stats import HealthPool
from src.entities.sprites import BaseSprite
from src.textures.texture_data import SingleTextureSpecs
from src.world.isometry.transforms import Transform

_BAR_INCREMENTS = 32

# This is not intended as a public variable, it just can't have an underscore prefix
# without causing the gc to choke and occasionally crash because of order of operations
# on garbage collection
full_bar: arcade.Texture | None = None


def _lazy_health_bar() -> arcade.Texture:
    global full_bar
    _full_bar = full_bar
    if _full_bar is None:
        _full_bar = SingleTextureSpecs.health_bar.loaded

    return _full_bar


@lru_cache(maxsize=_BAR_INCREMENTS)
def _crop_by_offset(offset: int):
    crop_start_x = _BAR_INCREMENTS + offset
    bar = _lazy_health_bar()
    return bar.crop(crop_start_x, 0, _BAR_INCREMENTS, bar.height)


def _get_crop(current: int, max_hp: int) -> arcade.Texture:
    offset: int = -round(math.floor((_BAR_INCREMENTS * current) / max_hp))
    return _crop_by_offset(offset)


class HealthBar:
    _full_bar: arcade.Texture
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
            self.sprite = arcade.Sprite(_get_crop(*self._state), scale=self._scale)
        else:
            self.sprite.texture = _get_crop(*self._state)
        self.sprite_list.clear()
        self.sprite_list.append(self.sprite)
        self.sprite.position = self._position

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
    _hidden: bool

    def __init__(
        self, fighter: Fighter, world_sprites: arcade.SpriteList, transform: Transform
    ):
        self._fighter = fighter
        self._health_bar = HealthBar(fighter.owner.entity_sprite.sprite.scale / 2)
        self._health_bar.set_watched_health(self._fighter.health)
        self._world_sprites = world_sprites
        self._hidden = True

        self._sprite = (
            BaseSprite(
                self._health_bar.sprite.normal_tex,
                scale=self._health_bar.sprite.scale,
            )
            .offset_anchor((0, 16))
            .set_transform(transform)
            .set_node(self._fighter.location)
        )

        self._world_sprites.append(self._sprite)

    def update(self):
        if self._fighter.incapacitated or self._hidden:
            self._sprite.visible = False
            return
        elif not self._hidden:
            self._sprite.visible = True

        self._health_bar.update()
        self._sprite.texture = self._health_bar.sprite.normal_tex
        self._sprite.set_node(self._fighter.location)

    @property
    def should_delete(self) -> bool:
        return self._fighter.incapacitated

    @property
    def attached_fighter(self) -> Fighter:
        return self._fighter

    def show(self):
        if self._fighter.incapacitated:
            return
        self._hidden = False

    def hide(self):
        self._hidden = True


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
