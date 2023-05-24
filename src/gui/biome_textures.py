from typing import NamedTuple

from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs

tiles = SpriteSheetSpecs.tiles.loaded


class Biome(NamedTuple):
    floor: list[Texture]
    wall: list[Texture]
    pillar: list[Texture]


class BiomeTextures(NamedTuple):
    @classmethod
    def castle(self):
        return Biome(
            floor=[tiles[88], tiles[89]],
            wall=[tiles[88], tiles[89]],
            pillar=[tiles[88], tiles[89]],
        )

    @classmethod
    def desert(self):
        return Biome(
            floor=[tiles[3], tiles[88]], wall=[tiles[3], tiles[88]], pillar=[tiles[42]]
        )

    @classmethod
    def snow(self):
        return Biome(
            floor=[tiles[22], tiles[89]],
            wall=[tiles[22], tiles[23], tiles[89]],
            pillar=[tiles[23]],
        )

    @property
    def exclusions(self):
        return []
