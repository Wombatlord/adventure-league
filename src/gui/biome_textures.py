from typing import NamedTuple

from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs

tiles = SpriteSheetSpecs.tiles.loaded


class BiomeName(NamedTuple):
    CASTLE = "castle"
    DESERT = "desert"
    SNOW = "snow"

    @classmethod
    def all_biomes(cls):
        return [cls.CASTLE, cls.DESERT, cls.SNOW]


class Biome(NamedTuple):
    FLOOR = "floor"
    WALL = "wall"
    PILLAR = "pillar"
    floor_tiles: list[Texture]
    wall_tiles: list[Texture]
    pillar_tiles: list[Texture]


class BiomeTextures(NamedTuple):
    @classmethod
    def castle(self):
        return Biome(
            floor_tiles=[tiles[88], tiles[89]],
            wall_tiles=[tiles[88], tiles[89]],
            pillar_tiles=[tiles[88], tiles[89]],
        )

    @classmethod
    def desert(self):
        return Biome(
            floor_tiles=[tiles[3], tiles[88]],
            wall_tiles=[tiles[3], tiles[88]],
            pillar_tiles=[tiles[42]],
        )

    @classmethod
    def snow(self):
        return Biome(
            floor_tiles=[tiles[22], tiles[89]],
            wall_tiles=[tiles[22], tiles[23], tiles[89]],
            pillar_tiles=[tiles[23]],
        )
