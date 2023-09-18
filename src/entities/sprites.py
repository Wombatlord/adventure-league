from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.biome_textures import BiomeName, BiomeTextures

if TYPE_CHECKING:
    from src.gui.animated_sprite_config import AnimatedSpriteConfig
    from src.entities.entity import Entity

import functools
import types
import weakref
from enum import Enum
from functools import cached_property
from typing import Any, Callable, Generic, Self, TypeVar

import arcade
from arcade import BasicSprite
from arcade.sprite import Sprite
from arcade.texture import Texture
from arcade.types import PathOrTexture, Point

from src.textures.flat_sprite_maps import flat_normal_map, flat_sprite_height_map
from src.world.isometry.transforms import Transform
from src.world.node import Node


class OffsetSprite(Sprite):
    px_offset: Point = (0, 0)

    def offset_anchor(self, px_offset: Point) -> Self:
        self.px_offset = px_offset
        return self

    @BasicSprite.position.getter
    def position(self) -> Point:
        base_pos = self._position
        return (
            base_pos[0] + self.px_offset[0] * self.scale,
            base_pos[1] + self.px_offset[1] * self.scale,
        )

    @position.setter
    def position(self, new_pos: Point) -> None:
        BasicSprite.position.fset(
            self,
            (
                new_pos[0] - self.px_offset[0],
                new_pos[1] - self.px_offset[1],
            ),
        )
        if hasattr(self, "_sync_list"):
            for sprite in self._sync_list:
                sprite.position = new_pos

    @BasicSprite.center_x.getter
    def center_x(self) -> float:
        return self._position[0] + self.px_offset[0] * self.scale

    @center_x.setter
    def center_x(self, x: float) -> None:
        new_pos = (
            x - self.px_offset[0] * self.scale,
            self._position[1],
        )
        BasicSprite.position.fset(
            self,
            (
                x - self.px_offset[0] * self.scale,
                self._position[1],
            ),
        )
        if hasattr(self, "_sync_list"):
            for sprite in self._sync_list:
                sprite.position = new_pos

    @BasicSprite.center_y.getter
    def center_y(self) -> float:
        return self._position[1] + self.px_offset[1] * self.scale

    @center_y.setter
    def center_y(self, y: float) -> None:
        new_pos = (
            self._position[0],
            y - self.px_offset[1] * self.scale,
        )

        BasicSprite.position.fset(
            self,
            new_pos,
        )

        if hasattr(self, "_sync_list"):
            for sprite in self._sync_list:
                sprite.position = new_pos


class BaseSprite(OffsetSprite, Sprite):
    transform: Transform

    def __init__(
        self,
        path_or_texture: PathOrTexture = None,
        scale: float = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        angle: float = 0.0,
        sync_list: tuple[arcade.Sprite, ...] = (),
        tile_type: int | None = None,
        **kwargs,
    ):
        super().__init__(
            path_or_texture,
            scale,
            center_x,
            center_y,
            angle,
            **kwargs,
        )

        self.animation_cycle = 0.75
        self.tex_idx = 0
        self.atk_cycle = 0
        self.owner = None
        self.transform = kwargs.get("transform", Transform.trivial())
        self._draw_priority = 0
        self._draw_priority_offset = kwargs.get("draw_priority_offset", 0)
        self._node = None
        self._sync_list = sync_list
        self.tile_type = tile_type

    def get_biome(self):
        if self.texture in BiomeTextures.castle().pillar_tiles:
            return BiomeName.CASTLE
        if self.texture in BiomeTextures.desert().pillar_tiles:
            return BiomeName.DESERT
        if self.texture in BiomeTextures.snow().pillar_tiles:
            return BiomeName.SNOW
        if self.texture in BiomeTextures.plains().pillar_tiles:
            return BiomeName.PLAINS

    @property
    def node(self) -> Node | None:
        return self._node

    def set_scale(self, scale: int):
        self.scale = scale
        for child in self._sync_list:
            if not hasattr(child, "set_scale"):
                continue
            child.set_scale(scale)

    def get_draw_priority(self) -> float:
        priority = self._draw_priority
        if self._node:
            priority = self.transform.draw_priority(self._node)
        return priority + self._draw_priority_offset

    def set_node(self, node: Node) -> Self:
        self._node = node

        for child in self._sync_list:
            if not hasattr(child, "set_node"):
                continue
            child.set_node(node)

        if self.transform != Transform.trivial():
            self.update_position()

        return self

    def set_transform(self, transform: Transform) -> Self:
        self.transform = transform
        for child in self._sync_list:
            if not hasattr(child, "set_transform"):
                continue
            child.set_transform(transform)
        if self._node:
            self.update_position()

        return self

    def update_position(self):
        self.center_x, self.center_y = self.transform.project(self._node)
        self._draw_priority = self.transform.draw_priority(self._node)
        for sprite in self._sync_list:
            if hasattr(sprite, "update_position"):
                sprite.update_position()

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        self.animation_cycle -= delta_time

        if self.animation_cycle <= 0:
            match self.tex_idx:
                case 0:
                    self.texture = self.textures[self.tex_idx]
                    self.tex_idx = (self.tex_idx + 1) % len(self.textures)
                    self.animation_cycle = 0.75

                case 1:
                    self.texture = self.textures[self.tex_idx]
                    self.tex_idx = (self.tex_idx + 1) % len(self.textures)
                    self.animation_cycle = 0.75
        for child in self._sync_list:
            if not hasattr(child, "update_animation"):
                continue
            child.update_animation(delta_time)

    def clone(self) -> Self:
        clone = BaseSprite(
            self.texture,
            self.scale,
            self.position[0],
            self.position[1],
            self.angle,
            tile_type=self.tile_type,
        )
        if self._node:
            clone.set_node(self._node)

        if self.transform:
            clone.set_transform(self.transform)

        return clone


SpriteType = TypeVar("SpriteType", arcade.Sprite, BaseSprite, OffsetSprite)


class MapSprite(Generic[SpriteType]):
    __sprite: SpriteType
    __tx_cache: dict[str, arcade.Texture]
    __recursion_canary: int

    def __init__(
        self, sprite: SpriteType, tx_map: Callable[[arcade.Texture], arcade.Texture]
    ):
        self.__sprite = sprite
        self.__map = tx_map
        self.__tx_cache = {}

    def __setattr__(self, key, value):
        if key == "texture":
            self.__sprite.texture = value
            if not self.__tx_cache.get(self.__sprite.texture.cache_name):
                self.__tx_cache[self.__sprite.texture.cache_name] = self.__map(
                    self.__sprite.texture
                )
        else:
            object.__setattr__(self, key, value)

    def __getattr__(self, item: str) -> Any:
        if item == "texture":
            if hit := self.__tx_cache.get(self.__sprite.texture.cache_name):
                return hit

            hit = self.__tx_cache[self.__sprite.texture.cache_name] = self.__map(
                self.__sprite.texture
            )
            return hit

        attr = getattr(self.__sprite, item)
        return attr


normal_maps: dict[str, weakref.ReferenceType[arcade.Texture]] = {}
height_maps: dict[str, weakref.ReferenceType[arcade.Texture]] = {}

_TxMap = Callable[[arcade.Texture], arcade.Texture]


def cache_aware(tx_map: _TxMap, cache: dict) -> _TxMap:
    @functools.wraps(tx_map)
    def _mapping(tex):
        nonlocal cache
        if tex.cache_name in cache:
            maybe_hit = cache[tex.cache_name]
            if hit := maybe_hit():
                return hit
            else:
                del cache[tex.cache_name]

        hit = tx_map(tex)
        cache[tex.cache_name] = weakref.ref(hit)
        return hit

    return _mapping


flat_sprite_height_map = cache_aware(flat_sprite_height_map, height_maps)
flat_normal_map = cache_aware(flat_normal_map, normal_maps)


def _apply(tx_map: _TxMap, sprite: SpriteType):
    mapped = sprite.clone()
    mapped.__dict__["_parent"] = sprite
    mapped.textures = [tx_map(tx) for tx in sprite.textures]
    mapped.texture = mapped.textures[mapped.tex_idx]

    return mapped


def z_mapped_sprite(sprite: SpriteType) -> SpriteType | MapSprite:
    return _apply(tx_map=flat_sprite_height_map, sprite=sprite)


def norm_mapped_sprite(sprite: SpriteType) -> SpriteType | MapSprite:
    return _apply(tx_map=flat_normal_map, sprite=sprite)


class AnimatedSpriteAttribute:
    sprite: BaseSprite

    @classmethod
    def from_sprite_conf(cls, sprite_conf: AnimatedSpriteConfig) -> Self:
        return cls(
            idle_textures=sprite_conf.idle_textures,
            attack_textures=sprite_conf.attack_textures,
        )

    def __init__(
        self,
        idle_textures: tuple[Texture, ...] = None,
        attack_textures: tuple[Texture, ...] = None,
        scale: float = 4,
        sprite_conf: AnimatedSpriteConfig | None = None,
    ) -> None:
        self.sprite_conf = sprite_conf

        self.normals = None
        self.heights = None
        sync_list = ()
        if self.sprite_conf:
            if normal_conf := self.sprite_conf.get_normals():
                self.normals = self.from_sprite_conf(normal_conf)
                self.normals.sprite.owner = self.normals
                sync_list += (self.normals.sprite,)

            if height_conf := self.sprite_conf.get_heights():
                self.heights = self.from_sprite_conf(height_conf)
                self.heights.sprite.owner = self.heights
                sync_list += (self.heights.sprite,)

        self._owner = None
        self.sprite = BaseSprite(scale=scale, sync_list=sync_list)
        self.sprite.owner = self
        self.idle_textures = idle_textures
        self.attack_textures = attack_textures
        self.all_textures = (
            [tex for tex in idle_textures],
            [tex.flip_left_right() for tex in idle_textures],
            [tex for tex in attack_textures],
            [tex.flip_left_right() for tex in attack_textures],
        )

        self.sprite.textures = self.all_textures[0]
        self.sprite.set_texture(0)

    @property
    def owner(self) -> Entity | None:
        return self._owner

    @owner.setter
    def owner(self, value: Entity):
        self._owner = value
        if self.normals:
            self.normals.owner = self.owner
        if self.heights:
            self.heights.owner = self.owner

    def offset_anchor(self, offset_px: Point) -> Self:
        self.sprite.offset_anchor(offset_px)
        if self.normals:
            self.normals.offset_anchor(offset_px)

        if self.heights:
            self.heights.offset_anchor(offset_px)
        return self

    def swap_idle_and_attack_textures(self):
        if self._owner.fighter.in_combat:
            self.sprite.textures = self.all_textures[2]
            self.sprite.set_texture(0)

        else:
            self.sprite.textures = self.all_textures[0]
            self.sprite.set_texture(0)

        if self.normals:
            self.normals.swap_idle_and_attack_textures()

        if self.heights:
            self.heights.swap_idle_and_attack_textures()

    def orient(self, orientation: Node):
        if isinstance(orientation, Enum):
            orientation = orientation.value

        match orientation:
            case (x, y) if isinstance(x, int) and isinstance(y, int):
                orientation = Node(*orientation)

        assert isinstance(
            orientation, Node
        ), f"expected type Node, got {type(orientation)=}"
        match orientation:
            case Node(0, 1) | Node(-1, 0):
                if self._owner.fighter.in_combat:
                    self.sprite.textures = self.all_textures[2]
                else:
                    self.sprite.textures = self.all_textures[1]
            case Node(1, 0) | Node(0, -1):
                if self._owner.fighter.in_combat:
                    self.sprite.textures = self.all_textures[3]
                else:
                    self.sprite.textures = self.all_textures[0]
            case _:
                pass

        self.sprite.set_texture(0)
        if self.normals:
            self.normals.orient(orientation)
        if self.heights:
            self.heights.orient(orientation)


class SimpleSpriteAttribute:
    sprite: BaseSprite

    def __init__(
        self,
        path_or_texture: Texture,
        scale: float = 4,
    ) -> None:
        self.owner = None
        self.sprite = BaseSprite(path_or_texture=path_or_texture, scale=scale)
        self.sprite.owner = self
        self.sprite.set_texture(0)

    def offset_anchor(self, offset_px: Point) -> Self:
        self.sprite.offset_anchor(offset_px)
        return self
