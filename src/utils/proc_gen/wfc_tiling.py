from enum import Enum
from typing import Callable, Literal, NamedTuple, Protocol, Self, TypeVar

import colorama
from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs
from src.utils.dice import D

CharTile = tuple[tuple[str, str, str], tuple[str, str, str], tuple[str, str, str]]

tiles = SpriteSheetSpecs.tiles.loaded


class TextureTiles:
    grass = tiles[1]
    ew = tiles[44]
    ns = tiles[45]
    nesw = tiles[48]
    se = tiles[51]
    ne = tiles[52]
    nw = tiles[53]
    sw = tiles[54]


class TileWeights:
    grass = 0.7
    straight = 0.5
    corner = 0.4
    cross = 0.2


T = Texture | CharTile


class Transform:
    def __init__(self, transform: Callable[[T], T]):
        self.transform = transform

    def __call__(self, t: T) -> T:
        return self.transform(t)

    def __mul__(self, other: Self) -> Self:
        a = Transform(lambda t: other.transform(self.transform(t)))
        return a


def identity(t: T) -> T:
    return t


###############
e = Transform(identity)


def variations(tile):
    transforms = (e, a, a * a, a * a * a, b, b * a, b * a * a, b * a * a * a)

    return [transform(tile) for transform in transforms]


meta_grid = (
    ("┌", "┐", " "),
    ("└", "┼", "─"),
    (" ", "│", " "),
)


def print_grid(grid: CharTile):
    a = "".join(grid[0]) + "\n"
    b = "".join(grid[1]) + "\n"
    c = "".join(grid[2]) + "\n"
    d = "".join(grid[3]) + "\n"
    e = "".join(grid[4]) + "\n"
    f = "".join(grid[5]) + "\n"
    g = "".join(grid[6]) + "\n"
    h = "".join(grid[7]) + "\n"
    i = "".join(grid[8]) + "\n"
    j = "".join(grid[9]) + "\n"
    final = (
        colorama.Fore.GREEN
        + f"{a}{b}{c}{d}{e}{f}{g}{h}{i}{j}"
        + colorama.Style.RESET_ALL
    )
    print(final)


Tile = TypeVar("Tile", bound=object)
Row = tuple[Tile, Tile, Tile]
Col = Row
Grid = tuple[Row, Row, Row]


class Reflection:
    @staticmethod
    def grid(grid: Grid) -> Grid:
        size = len(grid)
        return tuple(grid[i] for i in range(size - 1, -1, -1))

    @staticmethod
    def cell(cell: str) -> str:
        return {
            " ": " ",
            "┼": "┼",
            #
            "┌": "└",
            #
            "┐": "┘",
            #
            "└": "┌",
            #
            "┘": "┐",
            #
            "─": "─",
            "│": "│",
        }[cell]


class Rotation:
    @staticmethod
    def grid(grid: Grid) -> Grid:
        size = len(grid)
        col = lambda i: tuple(reversed([grid[j][i] for j in range(size)]))

        return tuple(col(k) for k in range(size))

    @staticmethod
    def cell(cell: str) -> str:
        return {
            " ": " ",
            "┼": "┼",
            "┌": "┐",
            "┐": "┘",
            "┘": "└",
            "└": "┌",
            "─": "│",
            "│": "─",
        }[cell]


def tile_map(symbol: str) -> Texture:
    return {
        " ": TextureTiles.grass,
        "┼": TextureTiles.nesw,
        "┌": TextureTiles.se,
        "┐": TextureTiles.sw,
        "┘": TextureTiles.nw,
        "└": TextureTiles.ne,
        "─": TextureTiles.ew,
        "│": TextureTiles.ns,
    }[symbol]


CellRot = Callable[[Tile], Tile]
CellRef = CellRot


def do_transform(grid: Grid[Tile], transform):
    rotated_grid = transform.grid(grid)

    row = lambda i: rotated_grid[i]

    return tuple(
        tuple(transform.cell(cell) for cell in row(i)) for i in range(len(grid))
    )


refl = lambda grid: do_transform(grid, transform=Reflection)
rot = lambda grid: do_transform(grid, transform=Rotation)

a = Transform(rot)
b = Transform(refl)

adjacency = (
    "──",
    "─┐",
    "┼┐",
    "┼─",
    "┌┐",
    "┌┘",
)
