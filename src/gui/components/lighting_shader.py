from __future__ import annotations

import time
from typing import Callable, Iterable

import arcade
from arcade.gl import geometry
from arcade.hitbox import HitBoxAlgorithm
from arcade.types import PointList
from PIL import Image
from pyglet.math import Mat4, Vec2, Vec3, Vec4

from src.entities.entity import Entity
from src.entities.sprites import (
    BaseSprite,
    MapSprite,
    norm_mapped_sprite,
    z_mapped_sprite,
)
from src.gui.biome_textures import BiomeName, biome_map
from src.textures.texture_data import SpriteSheetSpecs
from src.utils.shader_program import Binding, Shader
from src.world.isometry.transforms import Transform
from src.world.node import Node


class TrivialHitbox(HitBoxAlgorithm):
    cache = False

    def calculate(self, image: Image.Image, **kwargs) -> PointList:
        return (
            (0, 0),
            (image.size[0], 0),
            image.size,
            (0, image.size[1]),
        )


class ShaderPipeline:
    width: int
    height: int
    ctx: arcade.ArcadeContext
    terrain_nodes: list[Node]
    shader: Shader
    normal_binding: Binding
    scene_binding: Binding
    height_binding: Binding

    def __init__(
        self, width: int, height: int, window: arcade.Window, transform: Transform
    ):
        self.width = width
        self.height = height
        self.ctx = window.ctx
        self.time = time.time()
        self.transform = transform

        # render surface
        self.quad_fs = geometry.quad_2d_fs()

        self.shader = Shader(ctx=self.ctx)
        self.shader.load_sources(
            "./assets/shaders/height_mapped/frag.glsl",
            "./assets/shaders/height_mapped/vert.glsl",
        )

        # set up normal map texture/framebuffer pair
        self.normal_binding = self.shader.bind("norm", self.size)
        self.normal_toggle = 0.0

        # set up scene map texture/framebuffer pair
        self.scene_binding = self.shader.bind("scene", self.size)
        self.scene_toggle = 1.0

        # set up height map texture/frambuffer pair
        self.height_binding = self.shader.bind("height", self.size)
        self.height_toggle = 0.0

        self.terrain_size = (10, 10)
        self.terrain_binding = self.shader.bind("terrain", self.terrain_size)
        self.terrain_toggle = 0.0
        self.h_sprite = arcade.Sprite()
        self.h_sprite.texture = arcade.Texture(
            image=Image.new("RGBA", self.terrain_size),
            hit_box_algorithm=TrivialHitbox(),
        )
        self.ray_toggle = 0.0
        self.axes_toggle = 0.0

        # s2w = lambda: self.transform.screen_to_world() @ Mat4().scale(
        #     Vec3(self.width, self.height, 1.0)
        # )
        self.normal_biome = biome_map[BiomeName.NORMALS]
        self.height_biome = biome_map[BiomeName.HEIGHT]
        self.terrain_nodes = []
        self.normal_sprites = arcade.SpriteList()
        self.height_sprites = arcade.SpriteList()
        self.character_sprites = arcade.SpriteList()
        self.updating_sprite_mapping = {}
        self.shader.attach_uniform("scene_toggle", self.get_scene_toggle)
        self.shader.attach_uniform("height_toggle", self.get_height_toggle)
        self.shader.attach_uniform("normal_toggle", self.get_normal_toggle)
        self.shader.attach_uniform("ray_toggle", self.get_ray_toggle)
        self.shader.attach_uniform("axes_toggle", self.get_axes_toggle)
        self.shader.attach_uniform("terrain_toggle", self.get_terrain_toggle)
        self.shader.attach_uniform("pt_col", lambda: Vec4(0.8, 0.6, 0.2, 1.0))
        self.shader.attach_uniform("pt_src", lambda: Vec3(4.0, 4.0, 0.5))
        self.shader.attach_uniform(
            "directional_col", lambda: Vec4(*Vec3(1.0, 1.0, 0.5), 1.0)
        )
        self.shader.attach_uniform("directional_dir", lambda: Vec3(z=1.0, x=1.0, y=0.5))
        self.shader.attach_uniform("ambient_col", lambda: Vec4(1, 1, 1, 1))
        self.shader.attach_uniform("light_balance", lambda: Vec3(0.2, 0, 0.8))
        self.shader.attach_uniform("time_since_start", lambda: self.get_time())
        self.sprite_attributes = []
        self.init_empty_height_data()

    def init_empty_height_data(self):
        self.height_data = bytearray()
        self.height_data.extend((0 for _ in range(4 * 10 * 10)))

    def get_time(self) -> float:
        return time.time() - self.time

    def get_normal_toggle(self) -> float:
        return self.normal_toggle

    def get_axes_toggle(self) -> float:
        return self.axes_toggle

    def get_height_toggle(self) -> float:
        return self.height_toggle

    def get_scene_toggle(self) -> float:
        return self.scene_toggle

    def get_ray_toggle(self) -> float:
        return self.ray_toggle

    def get_terrain_toggle(self) -> float:
        return self.terrain_toggle

    def toggle_terrain(self):
        self.terrain_toggle = 1.0 - self.terrain_toggle

    def toggle_normal(self):
        self.normal_toggle = 1.0 - self.normal_toggle

    def toggle_scene(self):
        self.scene_toggle = 1.0 - self.scene_toggle

    def toggle_height(self):
        self.height_toggle = 1.0 - self.height_toggle

    def toggle_ray(self):
        self.ray_toggle = 1.0 - self.ray_toggle

    def toggle_axes(self):
        self.axes_toggle = 1.0 - self.axes_toggle

    def take_transform_from(self, get_transform: Callable[[], Mat4]):
        self.shader.attach_uniform("transform", get_transform)

    def locate_light_with(self, get_light_location: Callable[[], Vec3]):
        self.shader.attach_uniform("pt_src", get_light_location)

    def set_directional_light(self, colour: Vec4, direction: Vec3):
        self.shader.attach_uniform("directional_col", lambda: colour)
        self.shader.attach_uniform("directional_dir", lambda: direction)

    def set_light_balance(self, point: int = 1, directional: int = 1, ambient: int = 1):
        self.shader.attach_uniform(
            "light_balance", lambda: Vec3(ambient, directional, point)
        )

    def register_character_sprites(self, entities: list[Entity], clear: bool = True):
        if clear:
            self.clear_character_sprites()
        for entity in entities:
            self.sprite_attributes.append(entity.entity_sprite)
            normal_sprite = entity.entity_sprite.normals.sprite
            self.normal_sprites.append(normal_sprite)
            height_sprite = entity.entity_sprite.heights.sprite
            self.height_sprites.append(height_sprite)
            self.character_sprites.append(entity.entity_sprite.sprite)

    def clear_character_sprites(self):
        for sprite_attr in self.sprite_attributes:
            self.normal_sprites.remove(sprite_attr.normals.sprite)
            self.height_sprites.remove(sprite_attr.heights.sprite)
        self.character_sprites.clear()
        self.sprite_attributes.clear()

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    def update_terrain_nodes(self, sprites: arcade.SpriteList):
        sprite: BaseSprite
        self.normal_sprites.clear()
        self.height_sprites.clear()
        self.character_sprites.clear()
        nodes = {}
        max_x, max_y = 0, 0
        for sprite in sprites:
            if not hasattr(sprite, "clone") or not getattr(sprite, "node", None):
                continue
            clone: BaseSprite = sprite.clone()
            clone.texture = self.normal_biome.choose_texture_for_node(
                clone.node, clone.tile_type, sprite
            )
            clone.set_transform(sprite.transform)
            clone.set_node(sprite.node)
            nodes[clone.node[:2]] = max(nodes.get(clone.node[:2], -10), clone.node.z)
            max_x = max(clone.node.x, max_x)
            max_y = max(clone.node.y, max_y)

            self.normal_sprites.append(clone)

            height_clone: BaseSprite = sprite.clone()
            height_clone.set_transform(sprite.transform)
            height_clone.set_node(sprite.node)

            if clone.tile_type == 2 and sprite.biome != BiomeName.CASTLE:
                self.height_biome.assign_height_mapped_texture(height_clone, sprite)
            else:
                height_clone.texture = SpriteSheetSpecs.tile_height_map_sheet.loaded[
                    height_clone.node.z + 1
                ]

            self.height_sprites.append(height_clone)

        self._generate_world_height_tx(nodes)

    def refresh_draw_order(self):
        self.normal_sprites.sort(key=lambda s: s.get_draw_priority())
        self.height_sprites.sort(key=lambda s: s.get_draw_priority())

    def _generate_world_height_tx(self, nodes):
        self.height_data.clear()
        for xy in ((x, y) for y in range(10) for x in range(10)):
            x, y = xy
            if x >= 10 or y >= 10:
                continue
            z_node = nodes.get(xy, -1) + 1
            z_ground = z_node + 1
            z_mapped = 8 * z_ground
            self.height_data.extend((z_mapped, z_mapped, z_mapped, 255))

    def render_scene(self, sprite_list: arcade.SpriteList):
        self.refresh_draw_order()
        self.scene_binding.capture(lambda: sprite_list.draw(pixelated=True))
        self.normal_binding.capture(lambda: self.normal_sprites.draw(pixelated=True))
        self.height_binding.capture(lambda: self.height_sprites.draw(pixelated=True))
        self.terrain_binding.texture.write(
            self.height_data, level=0, viewport=(0, 0, 10, 10)
        )
        self.ctx.screen.use()
        with self.shader as program:
            self.quad_fs.render(program)

    def debug(self):
        breakpoint()
