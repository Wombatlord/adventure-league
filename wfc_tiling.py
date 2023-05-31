from typing import Literal

from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs

Up = tuple[Literal[1], Literal[0]]
Down = tuple[Literal[-1], Literal[0]]
Left = tuple[Literal[0], Literal[-1]]
Right = tuple[Literal[0], Literal[1]]

UP = (1, 0)
DOWN = (-1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
DIRS = [UP, DOWN, LEFT, RIGHT]

tiles = SpriteSheetSpecs.tiles.loaded


class Tiles:
    grass = tiles[1]
    straight_a = tiles[43]
    straight_b = tiles[44]
    cross = tiles[48]
    corner_one = tiles[51]
    corner_two = tiles[52]
    corner_three = tiles[53]
    corner_four = tiles[54]


class TileWeights:
    grass = 0.7
    straight = 0.5
    corner = 0.4
    cross = 0.2


class Symmetrys:
    grass = (
        (
            Tiles.grass,
            Tiles.straight_a,
            Tiles.cross,
            Tiles.corner_two,
            Tiles.corner_four,
        ),
    )

    @classmethod
    def grass_adjacent_rotations(cls, dir) -> tuple[Texture]:
        rotations = [cls.grass]
        if dir == UP:
            return cls.grass
        if dir == RIGHT:
            rotations[1] = Tiles.straight_b
            rotations[3] = Tiles.corner_one
            rotations[4] = Tiles.corner.three
        if dir == DOWN:
            rotations[3] = Tiles.corner_one
            rotations[4] = Tiles.corner_three
        if dir == LEFT:
            rotations[1] = Tiles.straight_b

        return tuple(rotations)
