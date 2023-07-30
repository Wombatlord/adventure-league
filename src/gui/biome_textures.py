import random
from typing import NamedTuple

from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs, SingleTextureSpecs
from src.world.node import Node

tiles = SpriteSheetSpecs.tiles.loaded
normals_tiles = SpriteSheetSpecs.tile_normals_2_layer.loaded


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

    def choose_texture_for_node(self, node: Node, tile_type: int) -> Texture:
        if self.name != BiomeName.NORMALS:
            return random.choice(self.get_tile_textures(tile_type))
        if node.z < 0:
            return self.floor_tiles[0]
        return self.floor_tiles[1]


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
            floor_tiles=normals_tiles,
            wall_tiles=normals_tiles,
            pillar_tiles=normals_tiles
        )


biome_map: dict[str, Biome] = {
    BiomeName.CASTLE: BiomeTextures.castle(),
    BiomeName.SNOW: BiomeTextures.snow(),
    BiomeName.DESERT: BiomeTextures.desert(),
    BiomeName.PLAINS: BiomeTextures.plains(),
    BiomeName.NORMALS: BiomeTextures.normal(),
}
