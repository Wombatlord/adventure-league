from enum import Enum
from typing import Self

from arcade import BasicSprite
from arcade.sprite import Sprite
from arcade.texture import Texture
from arcade.types import PathOrTexture, Point

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

    @BasicSprite.center_x.getter
    def center_x(self) -> float:
        return self._position[0] + self.px_offset[0] * self.scale

    @center_x.setter
    def center_x(self, x: float) -> None:
        BasicSprite.position.fset(
            self,
            (
                x - self.px_offset[0] * self.scale,
                self._position[1],
            ),
        )

    @BasicSprite.center_y.getter
    def center_y(self) -> float:
        return self._position[1] + self.px_offset[1] * self.scale

    @center_y.setter
    def center_y(self, y: float) -> None:
        BasicSprite.position.fset(
            self,
            (
                self._position[0],
                y - self.px_offset[1] * self.scale,
            ),
        )


class BaseSprite(OffsetSprite, Sprite):
    transform: Transform

    def __init__(
        self,
        path_or_texture: PathOrTexture = None,
        scale: float = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        angle: float = 0.0,
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

    def set_scale(self, scale: int):
        self.scale = scale

    def get_draw_priority(self) -> float:
        return self._draw_priority - self._draw_priority_offset

    def set_node(self, node: Node) -> Self:
        self._node = node
        if self.transform != Transform.trivial():
            self.update_position()

        return self

    def set_transform(self, transform: Transform) -> Self:
        self.transform = transform
        if self._node:
            self.update_position()

        return self

    def update_position(self):
        self.center_x, self.center_y = self.transform.project(self._node)
        self._draw_priority = self.transform.draw_priority(self._node)

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

    @property
    def node(self) -> Node:
        return self._node


class AnimatedSpriteAttribute:
    sprite: BaseSprite

    def __init__(
        self,
        idle_textures: tuple[Texture, ...] = None,
        attack_textures: tuple[Texture, ...] = None,
        scale: float = 4,
    ) -> None:
        self.owner = None
        self.sprite = BaseSprite(scale=scale)
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

    def offset_anchor(self, offset_px: Point) -> Self:
        self.sprite.offset_anchor(offset_px)
        return self

    def swap_idle_and_attack_textures(self):
        if self.owner.fighter.in_combat:
            self.sprite.textures = self.all_textures[2]
            self.sprite.set_texture(0)

        else:
            self.sprite.textures = self.all_textures[0]
            self.sprite.set_texture(0)

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
                if self.owner.fighter.in_combat:
                    self.sprite.textures = self.all_textures[2]
                else:
                    self.sprite.textures = self.all_textures[1]
            case Node(1, 0) | Node(0, -1):
                if self.owner.fighter.in_combat:
                    self.sprite.textures = self.all_textures[3]
                else:
                    self.sprite.textures = self.all_textures[0]
            case _:
                pass

        self.sprite.set_texture(0)


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
