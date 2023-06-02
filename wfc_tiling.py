from enum import Enum
from typing import Callable, Literal, NamedTuple, Protocol, Self, TypeVar

import colorama
from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs

CharTile = tuple[tuple[str, str, str], tuple[str, str, str], tuple[str, str, str]]

tiles = SpriteSheetSpecs.tiles.loaded


class TextureTiles:
    grass = tiles[1]
    ew = tiles[43]
    ns = tiles[44]
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


T = TypeVar("T", Texture, CharTile)


class Transform:
    def __init__(self, transform: Callable[[T], T]):
        self.transform = transform

    def __call__(self, t: T) -> T:
        return self.transform(t)

    def __mul__(self, other: Self) -> Self:
        a = Transform(lambda t: other.transform(self.transform(t)))
        return a


def rotate_symbols_in_grid(top_row, mid_row, btm_row) -> CharTile:
    top_left, top, top_right = rotate_symbols_in_row(top_row)
    left, mid, right = rotate_symbols_in_row(mid_row)
    btm_left, btm, btm_right = rotate_symbols_in_row(btm_row)

    return ((top_left, top, top_right), (left, mid, right), (btm_left, btm, btm_right))


def rotate_symbols_in_row(row) -> tuple[str, str, str]:
    l, m, r = row[0], row[1], row[2]

    if l == "|":
        l = "-"
    elif l == "-":
        l = "|"

    if m == "|":
        m = "-"
    elif m == "-":
        m = "|"

    if r == "|":
        r = "-"
    elif r == "-":
        r = "|"

    return l, m, r


def grid_ns_reflect(grid: CharTile) -> CharTile:
    reflected = [
        ["#", "#", "#"],
        ["#", "#", "#"],
        ["#", "#", "#"],
    ]

    top_l = grid[0][0]
    top_mid = grid[0][1]
    top_r = grid[0][2]

    btm_l = grid[2][0]
    btm_mid = grid[2][1]
    btm_r = grid[2][2]

    reflected[1][0] = grid[1][0]
    reflected[1][1] = grid[1][1]
    reflected[1][2] = grid[1][2]

    reflected[0][0] = btm_l
    reflected[0][1] = btm_mid
    reflected[0][2] = btm_r

    reflected[2][0] = top_l
    reflected[2][1] = top_mid
    reflected[2][2] = top_r

    reflected[0] = (*reflected[0],)
    reflected[1] = (*reflected[1],)
    reflected[2] = (*reflected[2],)

    return reflected


def grid_ew_reflect(grid: CharTile) -> CharTile:
    reflected = [
        ["#", "#", "#"],
        ["#", "#", "#"],
        ["#", "#", "#"],
    ]

    top_l = grid[0][0]
    mid_l = grid[1][0]
    btm_l = grid[2][0]

    top_r = grid[0][2]
    mid_r = grid[1][2]
    btm_r = grid[2][2]

    reflected[0][1] = grid[0][1]
    reflected[1][1] = grid[1][1]
    reflected[2][1] = grid[2][1]

    reflected[0][0] = top_r
    reflected[0][2] = top_l

    reflected[1][0] = mid_r
    reflected[1][2] = mid_l

    reflected[2][0] = btm_r
    reflected[2][2] = btm_l

    reflected[0] = (*reflected[0],)
    reflected[1] = (*reflected[1],)
    reflected[2] = (*reflected[2],)

    return (*reflected,)


def grid_rotate_cw(grid: CharTile) -> CharTile:
    top_row = [
        grid[0][0],
        grid[0][1],
        grid[0][2],
    ]
    mid_row = [
        grid[1][0],
        grid[1][1],
        grid[1][2],
    ]
    btm_row = [
        grid[2][0],
        grid[2][1],
        grid[2][2],
    ]

    (top, mid, btm) = rotate_symbols_in_grid(top_row, mid_row, btm_row)

    rotated = [
        ["#", "#", "#"],
        ["#", "#", "#"],
        ["#", "#", "#"],
    ]

    rotated[0][0], rotated[0][1], rotated[0][2] = btm[0], mid[0], top[0]
    rotated[1][0], rotated[1][1], rotated[1][2] = btm[1], mid[1], top[1]
    rotated[2][0], rotated[2][1], rotated[2][2] = btm[2], mid[2], top[2]

    return ((*rotated[0],), (*rotated[1],), (*rotated[2],))


def identity(t: T) -> T:
    return t


class GridTransforms:
    identity = Transform(identity)
    ns_reflect = Transform(grid_ns_reflect)
    rotate_once = Transform(lambda m: grid_rotate_cw(m))
    rotate_twice = rotate_once * rotate_once
    rotate_thrice = rotate_once * rotate_once * rotate_once

    @classmethod
    def variations(cls, grid):
        transforms = (
            cls.identity,
            cls.rotate_once,
            cls.rotate_twice,
            cls.rotate_thrice,
            cls.ns_reflect,
            cls.ns_reflect * cls.rotate_once,
            cls.ns_reflect * cls.rotate_twice,
            cls.ns_reflect * cls.rotate_thrice,
        )

        return [transform(grid) for transform in transforms]


def rotate_meta_grid_elements(rots, row, grid_row) -> list[CharTile]:
    for symbol in row:
        g = CharTiles.tiles[symbol]
        if rots == 1:
            g = GridTransforms.rotate_once(g)
        if rots == 2:
            g = GridTransforms.rotate_twice(g)
        if rots == 3:
            g = GridTransforms.rotate_thrice(g)
        grid_row.append(g)
    return grid_row


def construct_grids_from_meta_grid(m_grid, rots: int = 0) -> CharTile:
    top = m_grid[0]
    mid = m_grid[1]
    btm = m_grid[2]

    top_grids = rotate_meta_grid_elements(rots, top, [])
    mid_grids = rotate_meta_grid_elements(rots, mid, [])
    btm_grids = rotate_meta_grid_elements(rots, btm, [])

    return ((*top_grids,), (*mid_grids,), (*btm_grids,))


###############
adjacency = (
    # --
    (TextureTiles.ew, TextureTiles.ew),
    # -¬
    (TextureTiles.ew, TextureTiles.nw),
    # +¬
    (TextureTiles.nesw, TextureTiles.nw),
    # +-
    (TextureTiles.nesw, TextureTiles.ew),
    # ++ - Omitted
    # r¬
    (TextureTiles.se, TextureTiles.sw),
    # ~
    (TextureTiles.se, TextureTiles.nw),
)


def _a(t: Texture) -> Texture:
    tiles = {
        "-": [TextureTiles.ew, TextureTiles.ns, TextureTiles.ew, TextureTiles.ns],
        "+": [
            TextureTiles.nesw,
            TextureTiles.nesw,
            TextureTiles.nesw,
            TextureTiles.nesw,
        ],
        "¬": [TextureTiles.se, TextureTiles.ne, TextureTiles.nw, TextureTiles.sw],
    }
    family = None
    for fam, members in tiles.items():
        if t in members:
            family = fam

    target = (tiles[family].index(t) + 1) % 4
    return tiles[family][target]


def _b(t: Texture) -> Texture:
    reflections = [
        (TextureTiles.ns, TextureTiles.ns),
        (TextureTiles.ew, TextureTiles.ew),
        (TextureTiles.nesw, TextureTiles.nesw),
        (TextureTiles.se, TextureTiles.sw),
        (TextureTiles.ne, TextureTiles.nw),
    ]

    for one, tother in reflections:
        if t == one:
            return tother
        else:
            return one


a = Transform(_a)
b = Transform(_b)
e = Transform(identity)


def variations(tile):
    transforms = (e, a, a * a, a * a * a, b, b * a, b * a * a, b * a * a * a)

    return [transform(tile) for transform in transforms]


class CharTiles:
    grass = (
        ("#", "#", "#"),
        ("#", "#", "#"),
        ("#", "#", "#"),
    )

    ew = (
        ("#", "#", "#"),
        ("-", "-", "-"),
        ("#", "#", "#"),
    )

    se = (
        ("#", "#", "#"),
        ("#", "+", "-"),
        ("#", "|", "#"),
    )

    nesw = (
        ("#", "|", "#"),
        ("-", "+", "-"),
        ("#", "|", "#"),
    )

    tiles = {
        "-": ew,
        "-m": ew,
        "|": GridTransforms.rotate_once(ew),
        "|m": GridTransforms.rotate_once(ew),
        "¬": se,
        "¬1": GridTransforms.rotate_once(se),
        "¬2": GridTransforms.rotate_twice(se),
        "¬3": GridTransforms.ns_reflect(se),
        "+": nesw,
        "#": grass,
    }


meta_grid = (
    ("¬", "¬1", "#"),
    ("¬3", "+", "-m"),
    ("#", "|m", "#"),
)


def print_grid(grid: CharTile):
    top = "".join(grid[0]) + "\n"
    mid = "".join(grid[1]) + "\n"
    btm = "".join(grid[2])

    final = colorama.Fore.GREEN + f"{top}{mid}{btm}" + colorama.Style.RESET_ALL
    print(final)


def print_grids_horizontal(grids: list[CharTile]):
    top = ""
    mid = ""
    btm = ""

    for grid in grids:
        top += "".join(grid[0]) + " "
        mid += "".join(grid[1]) + " "
        btm += "".join(grid[2]) + " "

    final = colorama.Fore.GREEN + f"{top}\n{mid}\n{btm}" + colorama.Style.RESET_ALL
    print(final)


v = GridTransforms.variations(CharTiles.se)

for grid in v:
    print_grid(grid)
    print()

m_grid_0 = construct_grids_from_meta_grid(meta_grid)

m_rotated = GridTransforms.rotate_once(meta_grid)
m_grid_1 = construct_grids_from_meta_grid(m_rotated, 1)

m_rotated = GridTransforms.rotate_twice(meta_grid)
m_grid_2 = construct_grids_from_meta_grid(m_rotated, 2)

m_rotated = GridTransforms.rotate_thrice(meta_grid)
m_grid_3 = construct_grids_from_meta_grid(m_rotated, 3)

print_grids_horizontal(m_grid_0[0])
print_grids_horizontal(m_grid_0[1] + (meta_grid,))
print_grids_horizontal(m_grid_0[2])
print()
print_grids_horizontal(m_grid_1[0] + m_grid_2[0] + m_grid_3[0])
print_grids_horizontal(m_grid_1[1] + m_grid_2[1] + m_grid_3[1])
print_grids_horizontal(m_grid_1[2] + m_grid_2[2] + m_grid_3[2])
