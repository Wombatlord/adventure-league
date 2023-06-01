from enum import Enum
from typing import Callable, Literal, NamedTuple, Protocol, Self, TypeVar

import colorama
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


class Symmetrys:
    grass = (
        Tiles.grass,
        Tiles.ew,
        Tiles.nesw,
        Tiles.ne,
        Tiles.sw,
    )

    @classmethod
    def grass_adjacent_rotations(cls, dir) -> tuple[Texture]:
        rotations = [cls.grass]
        if dir == UP:
            return cls.grass
        if dir == RIGHT:
            rotations[1] = Tiles.ns
            rotations[3] = Tiles.se
            rotations[4] = Tiles.corner.three
        if dir == DOWN:
            rotations[3] = Tiles.se
            rotations[4] = Tiles.nw
        if dir == LEFT:
            rotations[1] = Tiles.ns

        return tuple(rotations)


###############
adjacency = (
    # --
    (Tiles.ew, Tiles.ew),
    # -¬
    (Tiles.ew, Tiles.nw),
    # +¬
    (Tiles.nesw, Tiles.nw),
    # +-
    (Tiles.nesw, Tiles.ew),
    # ++ - Omitted
    # r¬
    (Tiles.se, Tiles.sw),
    # ~
    (Tiles.se, Tiles.nw),
)


def _a(t: Texture) -> Texture:
    tiles = {
        "-": [Tiles.ew, Tiles.ns, Tiles.ew, Tiles.ns],
        "+": [Tiles.nesw, Tiles.nesw, Tiles.nesw, Tiles.nesw],
        "¬": [Tiles.se, Tiles.ne, Tiles.nw, Tiles.sw],
    }
    family = None
    for fam, members in tiles.items():
        if t in members:
            family = fam

    target = (tiles[family].index(t) + 1) % 4
    return tiles[family][target]


def _b(t: Texture) -> Texture:
    reflections = [
        (Tiles.ns, Tiles.ns),
        (Tiles.ew, Tiles.ew),
        (Tiles.nesw, Tiles.nesw),
        (Tiles.se, Tiles.sw),
        (Tiles.ne, Tiles.nw),
    ]

    for one, tother in reflections:
        if t == one:
            return tother
        else:
            return one


def identity(t: Texture) -> Texture:
    return t


class Transform:
    def __init__(self, transform: Callable[[Texture], Texture]):
        self.transform = transform

    def __call__(self, t: Texture) -> Texture:
        self.transform(t)

    def __mul__(self, other: Self) -> Self:
        a = Transform()
        a.transform = lambda t: other.transform(self.transform(t))
        return a


a = Transform(_a)
b = Transform(_b)
e = Transform(identity)


def variations(tile):
    transforms = (e, a, a * a, a * a * a, b, b * a, b * a * a, b * a * a * a)

    return [transform(tile) for transform in transforms]


#
#               ###
#               -+#
#               #|#
#
#  ### #|#      #|#
#  --- -+#  =>  #|#
#  ### ###      #|#
#
#
#
Grid = tuple[tuple[str, str, str], tuple[str, str, str], tuple[str, str, str]]

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


def print_grid(grid: Grid):
    a = "".join(grid[0]) + "\n"
    b = "".join(grid[1]) + "\n"
    c = "".join(grid[2])

    final = colorama.Fore.GREEN + f"{a}{b}{c}" + colorama.Style.RESET_ALL
    print(final)


def print_grids_horizontal(grids: list[Grid]):
    a1 = ""
    a2 = ""
    c3 = ""

    for grid in grids:
        a1 += "".join(grid[0]) + " "
        a2 += "".join(grid[1]) + " "
        c3 += "".join(grid[2]) + " "

    final = colorama.Fore.GREEN + f"{a1}\n{a2}\n{c3}" + colorama.Style.RESET_ALL
    print(final)


def grid_ew_reflect(grid: Grid) -> Grid:
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


def grid_ns_reflect(grid: Grid) -> Grid:
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


def grid_rotate_cw(grid: Grid) -> Grid:
    rotated = [
        ["#", "#", "#"],
        ["#", "#", "#"],
        ["#", "#", "#"],
    ]

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

    rotated[0][0] = btm[0]
    rotated[0][1] = mid[0]
    rotated[0][2] = top[0]
    rotated[1][0] = btm[1]
    rotated[1][1] = mid[1]
    rotated[1][2] = top[1]
    rotated[2][0] = btm[2]
    rotated[2][1] = mid[2]
    rotated[2][2] = top[2]

    rotated[0] = (*rotated[0],)
    rotated[1] = (*rotated[1],)
    rotated[2] = (*rotated[2],)

    return (*rotated,)


def rotate_symbols_in_grid(top_row, mid_row, btm_row) -> Grid:
    top_left, top, top_right = rotate_symbols_in_row(top_row)
    left, mid, right = rotate_symbols_in_row(mid_row)
    btm_left, btm, btm_right = rotate_symbols_in_row(btm_row)

    return ((top_left, top, top_right), (left, mid, right), (btm_left, btm, btm_right))


def rotate_symbols_in_row(row) -> tuple[str, str, str]:
    l = row[0]
    m = row[1]
    r = row[2]

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


grid = {
    "-": ew,
    "-m": ew,
    "|": grid_rotate_cw(ew),
    "|m": grid_rotate_cw(ew),
    "¬": se,
    "¬1": grid_rotate_cw(se),
    "¬2": grid_rotate_cw(grid_rotate_cw(se)),
    "¬3": grid_ns_reflect(se),
    "+": nesw,
    "#": grass,
}

meta_grid = (
    ("¬", "¬1", "#"),
    ("¬3", "+", "-m"),
    ("#", "|m", "#"),
)


def meta_grid_element_rotate(m_grid, rots: int = 0) -> Grid:
    top = m_grid[0]
    mid = m_grid[1]
    btm = m_grid[2]

    top_grids = element_rotate(rots, top, [])
    mid_grids = element_rotate(rots, mid, [])
    btm_grids = element_rotate(rots, btm, [])

    return ((*top_grids,), (*mid_grids,), (*btm_grids,))


def element_rotate(rots, row, grid_row) -> list[Grid]:
    for symbol in row:
        g = grid[symbol]
        if rots == 1:
            g = grid_rotate_cw(g)
        if rots == 2:
            g = grid_rotate_cw(grid_rotate_cw(g))
        if rots == 3:
            g = grid_rotate_cw(grid_rotate_cw(grid_rotate_cw(g)))
        grid_row.append(g)
    return grid_row


meta_grid_rotated = meta_grid_element_rotate(grid_rotate_cw(meta_grid), rots=1)
meta_grid_rotated_twice = meta_grid_element_rotate(
    grid_rotate_cw(grid_rotate_cw(meta_grid)), rots=2
)
meta_grid_rotated_thrice = meta_grid_element_rotate(
    grid_rotate_cw(grid_rotate_cw(grid_rotate_cw(meta_grid))), rots=3
)
m_grid = meta_grid_element_rotate(meta_grid, rots=0)

top_row = (
    meta_grid_rotated[0] + meta_grid_rotated_twice[0] + meta_grid_rotated_thrice[0]
)
mid_row = (
    meta_grid_rotated[1] + meta_grid_rotated_twice[1] + meta_grid_rotated_thrice[1]
)
btm_row = (
    meta_grid_rotated[2] + meta_grid_rotated_twice[2] + meta_grid_rotated_thrice[2]
)

print_grids_horizontal(m_grid[0])
print_grids_horizontal(m_grid[1])
print_grids_horizontal(m_grid[2])
print()
print_grids_horizontal(top_row)
print_grids_horizontal(mid_row)
print_grids_horizontal(btm_row)

# row_one = [se, grid_rotate_cw(se)]
# row_two = [grid_rotate_cw(grid_rotate_cw(se)), grid_ns_reflect(se)]


# print("\n" + colorama.Fore.YELLOW + "Rotated Corners")
# print(" E   A  ")
# print_grids_horizontal(row_one)
# print(colorama.Fore.YELLOW + " A2  B ")
# print_grids_horizontal(row_two)