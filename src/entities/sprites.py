from arcade.sprite import Sprite
from arcade.texture import Texture
from enum import Enum

from src.entities.locatable import Node


class BaseSprite(Sprite):
    def __init__(
        self,
        scale: float = 4,
    ):
        super().__init__(scale=scale)

        self.animation_cycle = 0.05
        self.tex_idx = 0
        self.owner = None

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        self.animation_cycle -= delta_time
        if self.animation_cycle <= 0:
            match self.tex_idx:
                case 0:
                    self.texture = self.textures[self.tex_idx]
                    self.tex_idx = (self.tex_idx + 1) % len(self.textures)
                    self.animation_cycle = 0.05
            
                case 1:
                    self.texture = self.textures[self.tex_idx]
                    self.tex_idx = (self.tex_idx + 1) % len(self.textures)
                    self.animation_cycle = 0.05


class EntitySprite:
    def __init__(
        self,
        idle_textures: tuple[Texture, ...] = None,
        scale: float = 4,
    ) -> None:
        self.owner = None
        self.sprite = BaseSprite(scale=scale)
        self.sprite.owner = self
        self.idle_textures = idle_textures
        self.all_textures = (
            [tex for tex in idle_textures],
            [tex.flip_left_to_right() for tex in idle_textures],
        )

        self.sprite.textures = self.all_textures[0]
        self.sprite.set_texture(0)
    
    
    def orient(self, orientation: Node):
        if isinstance(orientation, Enum):
            orientation = orientation.value

        assert isinstance(orientation, Node)
        match orientation:
            case Node(0, 1) | Node(-1, 0):
                self.sprite.textures = self.all_textures[1]
            case Node(1, 0) | Node(0, -1):
                self.sprite.textures = self.all_textures[0]
            case _:
                pass

        self.sprite.set_texture(0)