from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.components.lighting_shader import ShaderPipeline

import random
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from src.entities.sprites import BaseSprite

from arcade import Texture
from pyglet.math import Vec3, Vec4

from src.textures.texture_data import SingleTextureSpecs, SpriteSheetSpecs
from src.world.node import Node

tiles = SpriteSheetSpecs.tiles.loaded
normals_tile = SingleTextureSpecs.tile_normals.loaded
normals_pillars = SpriteSheetSpecs.pillar_normals.loaded


class BiomeName:
    CASTLE = "castle"
    DESERT = "desert"
    SNOW = "snow"
    PLAINS = "plains"
    NORMALS = "normals"

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
    pillar_tiles: list[Texture]
    name: str

    def get_tile_textures(self, tile_type: int) -> list[Texture]:
        return self[tile_type]

    def choose_tile_texture(self, tile_type: int) -> Texture:
        return random.choice(self.get_tile_textures(tile_type))

    def choose_texture_for_node(
        self, node: Node, tile_type: int, sprite: BaseSprite
    ) -> Texture:
        if self.name != BiomeName.NORMALS:
            return random.choice(self.get_tile_textures(tile_type))

        biome = sprite.get_biome()
        match tile_type:
            case 0:
                return self.floor_tiles[0]
            case 1:
                return self.wall_tiles[0]
            case 2:
                if biome == BiomeName.CASTLE:
                    return self.floor_tiles[0]
                if biome == BiomeName.DESERT:
                    return self.get_pillar_normal(
                        sprite.texture, biome, BiomeTextures.desert().pillar_tiles
                    )
                if biome == BiomeName.SNOW:
                    return self.get_pillar_normal(
                        sprite.texture, biome, BiomeTextures.snow().pillar_tiles
                    )
                if biome == BiomeName.PLAINS:
                    return self.get_pillar_normal(
                        sprite.texture, biome, BiomeTextures.plains().pillar_tiles
                    )

    def get_pillar_normal(self, texture, biome, biome_tiles):
        for tx in biome_tiles:
            if texture == tx:
                return self.pillar_tiles[biome][biome_tiles.index(tx)]

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


biome_map: dict[str, Biome] = {
    BiomeName.CASTLE: BiomeTextures.castle(),
    BiomeName.SNOW: BiomeTextures.snow(),
    BiomeName.DESERT: BiomeTextures.desert(),
    BiomeName.PLAINS: BiomeTextures.plains(),
    BiomeName.NORMALS: BiomeTextures.normal(),
}
