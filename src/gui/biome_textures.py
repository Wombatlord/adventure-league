from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from src.gui.components.lighting_shader import ShaderPipeline
    from src.entities.sprites import BaseSprite

import random

from arcade import Texture
from pyglet.math import Vec3, Vec4

from src.textures.texture_data import SingleTextureSpecs, SpriteSheetSpecs
from src.world.node import Node

tiles = SpriteSheetSpecs.tiles.loaded
normals_tile = SingleTextureSpecs.tile_normals.loaded
normals_pillars = SpriteSheetSpecs.pillar_normals.loaded
heights_pillars = SpriteSheetSpecs.pillar_heights.loaded


class BiomeName:
    CASTLE = "castle"
    DESERT = "desert"
    SNOW = "snow"
    PLAINS = "plains"
    NORMALS = "normals"
    HEIGHT = "heights"

    @classmethod
    def all_biomes(cls) -> list[str]:
        return [cls.CASTLE, cls.DESERT, cls.SNOW, cls.PLAINS]


class TileTypes:
    FLOOR = 0
    WALL = 1
    PILLAR = 2


class Biome(NamedTuple):
    floor_tiles: list[Texture]
    wall_tiles: list[Texture]
    pillar_tiles: list[Texture] | dict[str, list[Texture]]
    name: str

    def get_tile_textures(self, tile_type: int) -> list[Texture]:
        return self[tile_type]

    def choose_tile_texture(self, tile_type: int) -> Texture:
        return random.choice(self.get_tile_textures(tile_type))

    def assign_height_mapped_texture(
        self, clone_sprite: BaseSprite, origin_sprite: BaseSprite
    ):
        biome = origin_sprite.get_biome()
        match biome:
            case BiomeName.CASTLE:
                clone_sprite.texture = self.get_pillar_height_map_texture(
                    BiomeTextures.castle().pillar_tiles, origin_sprite.texture, biome
                )
            case BiomeName.DESERT:
                clone_sprite.texture = self.get_pillar_height_map_texture(
                    BiomeTextures.desert().pillar_tiles, origin_sprite.texture, biome
                )
            case BiomeName.SNOW:
                clone_sprite.texture = self.get_pillar_height_map_texture(
                    BiomeTextures.snow().pillar_tiles, origin_sprite.texture, biome
                )
            case BiomeName.PLAINS:
                clone_sprite.texture = self.get_pillar_height_map_texture(
                    BiomeTextures.plains().pillar_tiles, origin_sprite.texture, biome
                )

    def get_pillar_height_map_texture(
        self, biome_pillar_tiles: list[Texture], texture: Texture, biome_name: str
    ) -> Texture:
        return self.pillar_tiles[f"{biome_name}"][biome_pillar_tiles.index(texture)]

    def choose_texture_for_node(
        self, node: Node, tile_type: int, sprite: BaseSprite
    ) -> Texture:
        if self.name != BiomeName.NORMALS:
            return random.choice(self.get_tile_textures(tile_type))

        biome = sprite.get_biome()
        match tile_type:
            case TileTypes.FLOOR:
                return self.floor_tiles[0]
            case TileTypes.WALL:
                return self.wall_tiles[0]
            case TileTypes.PILLAR:
                return self.check_biome_for_pillar_normal(biome, sprite.texture)

    def check_biome_for_pillar_normal(self, biome: str, texture: Texture):
        match biome:
            case BiomeName.CASTLE:
                return self.floor_tiles[0]
            case BiomeName.DESERT:
                return self.get_pillar_normal(
                    texture, biome, BiomeTextures.desert().pillar_tiles
                )
            case BiomeName.SNOW:
                return self.get_pillar_normal(
                    texture, biome, BiomeTextures.snow().pillar_tiles
                )
            case BiomeName.PLAINS:
                return self.get_pillar_normal(
                    texture, biome, BiomeTextures.plains().pillar_tiles
                )

    def get_pillar_normal(
        self, texture: Texture, biome_name: str, biome_pillar_tiles: list[Texture]
    ) -> Texture:
        return self.pillar_tiles[f"{biome_name}"][biome_pillar_tiles.index(texture)]

    def biome_lighting(self, shader_pipeline: ShaderPipeline):
        match self.name:
            case BiomeName.SNOW:
                shader_pipeline.set_directional_light(
                    Vec4(0.4, 0.3, 0.8, 1), Vec3(1, 1, 1)
                )
                shader_pipeline.set_light_balance(point=1, directional=1, ambient=0.2)

            case BiomeName.CASTLE:
                shader_pipeline.set_directional_light(
                    Vec4(0.4, 0.2, 0, 1), Vec3(1, 1, 1)
                )
                shader_pipeline.set_light_balance(point=1, directional=1, ambient=0.2)

            case BiomeName.DESERT:
                shader_pipeline.set_directional_light(
                    Vec4(0.6, 0.6, 0, 1), Vec3(1, 1, 1)
                )
                shader_pipeline.set_light_balance(point=1, directional=1, ambient=0.2)

            case BiomeName.PLAINS:
                shader_pipeline.set_directional_light(
                    Vec4(0.5, 0.5, 0.5, 1), Vec3(1, 1, 1)
                )
                shader_pipeline.set_light_balance(point=1, directional=1, ambient=0.2)


class BiomeTextures:
    @classmethod
    def castle(cls):
        return Biome(
            name=BiomeName.CASTLE,
            floor_tiles=[tiles[88], tiles[89]],
            wall_tiles=[tiles[88], tiles[89]],
            pillar_tiles=[tiles[88], tiles[89]],
        )

    @classmethod
    def desert(cls):
        return Biome(
            name=BiomeName.DESERT,
            floor_tiles=[tiles[3], tiles[88]],
            wall_tiles=[tiles[3], tiles[88]],
            pillar_tiles=[tiles[42], tiles[31], tiles[9], tiles[8], tiles[20]],
        )

    @classmethod
    def snow(cls):
        return Biome(
            name=BiomeName.SNOW,
            floor_tiles=[tiles[22], tiles[23], tiles[89]],
            wall_tiles=[tiles[22], tiles[23], tiles[89]],
            pillar_tiles=[tiles[32], tiles[43], tiles[20]],
        )

    @classmethod
    def plains(cls):
        return Biome(
            name=BiomeName.PLAINS,
            floor_tiles=[tiles[0], tiles[1], tiles[25]],
            wall_tiles=[tiles[0], tiles[1]],
            pillar_tiles=[
                tiles[30],
                tiles[41],
                tiles[9],
                tiles[8],
                tiles[19],
                tiles[10],
            ],
        )

    @classmethod
    def normal(cls):
        return Biome(
            name=BiomeName.NORMALS,
            floor_tiles=[normals_tile],
            wall_tiles=[normals_tile],
            pillar_tiles={
                BiomeName.DESERT: [
                    normals_pillars[42],
                    normals_pillars[31],
                    normals_pillars[9],
                    normals_pillars[8],
                    normals_pillars[20],
                ],
                BiomeName.SNOW: [
                    normals_pillars[32],
                    normals_pillars[43],
                    normals_pillars[20],
                ],
                BiomeName.PLAINS: [
                    normals_pillars[30],
                    normals_pillars[41],
                    normals_pillars[9],
                    normals_pillars[8],
                    normals_pillars[19],
                    normals_pillars[10],
                ],
            },
        )

    @classmethod
    def height(cls):
        return Biome(
            name=BiomeName.HEIGHT,
            floor_tiles=[],
            wall_tiles=[],
            pillar_tiles={
                BiomeName.CASTLE: [
                    tiles[88],
                    tiles[89],
                ],
                BiomeName.DESERT: [
                    heights_pillars[42],
                    heights_pillars[31],
                    heights_pillars[9],
                    heights_pillars[8],
                    heights_pillars[20],
                ],
                BiomeName.SNOW: [
                    heights_pillars[32],
                    heights_pillars[43],
                    heights_pillars[20],
                ],
                BiomeName.PLAINS: [
                    heights_pillars[30],
                    heights_pillars[41],
                    heights_pillars[9],
                    heights_pillars[8],
                    heights_pillars[19],
                    heights_pillars[10],
                ],
            },
        )


biome_map: dict[str, Biome] = {
    BiomeName.CASTLE: BiomeTextures.castle(),
    BiomeName.SNOW: BiomeTextures.snow(),
    BiomeName.DESERT: BiomeTextures.desert(),
    BiomeName.PLAINS: BiomeTextures.plains(),
    BiomeName.NORMALS: BiomeTextures.normal(),
    BiomeName.HEIGHT: BiomeTextures.height(),
}
