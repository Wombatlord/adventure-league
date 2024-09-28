import numpy as np

from src.utils.printer import Printer
from src.utils.proc_gen.data_textures.data_texture import DataTexture

TILE_X = np.array([10, 0], dtype=int)
TILE_Y = np.array([0, 10], dtype=int)
TILE_SHAPE = TILE_X + TILE_Y
CANVAS_SHAPE = TILE_SHAPE * 3


def gen_open_ground() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    arr = dt.pixels
    arr[:, :] = [8, 8, 8, 255]
    return dt


def gen_spike() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    arr = dt.pixels
    arr[:, :] = [8, 8, 8, 255]
    for border in range(1, 5):
        arr[border:-border, border:-border, :3] = border + 8
    arr[:, :, 3] = 255
    return dt


def gen_ice_pillars() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    arr = dt.pixels
    ground = 8
    short = 12
    tall = 15
    arr[:, :] = [ground, ground, ground, 255]

    arr[2:5, 4:7, :3] = tall
    arr[5:8, 3:6, :3] = short

    return dt


def gen_tall_cactus() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    tall = 16
    dt.pixels[:, :, :3] = ground
    dt.pixels[:, :, 3] = 255
    dt.pixels[3:6, 3:6, :3] = tall

    return dt


def gen_short_cactus() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    tall = 12
    dt.pixels[:, :, :3] = ground
    dt.pixels[:, :, 3] = 255
    dt.pixels[2:7, 2:7, :3] = tall

    return dt


def gen_rock() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    edge = 14
    tall = 16
    mid = 12
    dt.pixels[:, :, :3] = ground
    dt.pixels[:, :, 3] = 255
    dt.pixels[1:8, 4, :3] = mid
    dt.pixels[2:7, 4, :3] = edge
    dt.pixels[3:6, 4, :3] = tall
    dt.pixels[3:6, 5, :3] = mid
    return dt


def gen_split_rock() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    top_tier = 16
    second_tier = 14
    third_tier = 12
    fourth_tier = 10

    dt.pixels[:, :, 3] = 255
    dt.pixels[:, :, :3] = ground
    dt.pixels[1:9, 4, :3] = third_tier
    dt.pixels[5, 4, :3] = fourth_tier
    dt.pixels[3, 4, :3] = top_tier
    dt.pixels[2, 4, :3], dt.pixels[4, 4, :3], dt.pixels[7, 4, :3] = (
        second_tier,
        second_tier,
        second_tier,
    )

    return dt


def gen_reeds() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    top = 16
    mid = 14
    low = 10

    dt.pixels[:, :, 3] = 255
    dt.pixels[:, :, :3] = ground
    dt.pixels[2:8, 4, :3] = low
    dt.pixels[4, 4, :3] = top
    dt.pixels[6, 4, :3] = mid

    return dt


def gen_yellow_shrub() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    top = 16
    mid = 14
    low = 10

    dt.pixels[:, :, 3] = 255
    dt.pixels[:, :, :3] = ground
    dt.pixels[2:9, 4, :3] = mid
    dt.pixels[5, 4, :3] = top
    dt.pixels[3:5, 4, :3], dt.pixels[7, 4, :3] = low, low

    return dt


def gen_brown_shrub() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    top = 16
    mid = 14
    low = 10

    dt.pixels[:, :, 3] = 255
    dt.pixels[:, :, :3] = ground
    dt.pixels[1:9, 4, :3] = top
    dt.pixels[2, 4, :3], dt.pixels[7, 4, :3] = mid, mid
    dt.pixels[4, 4, :3] = low

    return dt


def gen_green_shrub() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    top = 16
    mid = 14
    mid_b = 12
    low = 10

    dt.pixels[:, :, 3] = 255
    dt.pixels[:, :, :3] = ground
    dt.pixels[1:9, 4, :3] = low
    dt.pixels[2:9, 4, :3] = mid_b
    dt.pixels[3:8, 4, :3] = mid
    dt.pixels[4:7, 4, :3] = top

    return dt


def white_square() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    dt.pixels[:, :] = [255] * 4
    return dt


def render_data_texture_to_terminal(*args):
    args = [*args]
    mode = "color"
    if args:
        mode = args.pop(0)

    mapping = {
        (0, 0): gen_green_shrub(),
        (0, 1): gen_yellow_shrub(),
        (0, 2): gen_brown_shrub(),
        (1, 0): gen_ice_pillars(),
        (1, 1): gen_spike(),
        (1, 2): gen_reeds(),
        (2, 0): gen_rock(),
        (2, 1): gen_tall_cactus(),
        (2, 2): gen_split_rock(),
    }

    display = DataTexture(CANVAS_SHAPE, dtype=np.uint8)
    display.pixels[:, :] = [0, 0, 0, 255]

    for x, y in (
        (x_, y_)
        for y_ in range(display.pixels.shape[0])
        for x_ in range(display.pixels.shape[1])
    ):
        tx_rgba = np.array([80, 80, 80, 255], dtype=np.uint8)
        for loffset, tex in mapping.items():
            offset = loffset[0] * TILE_X + loffset[1] * TILE_Y
            i_x, i_y = x - offset[0], y - offset[1]

            if 0 <= i_x < 10 and 0 <= i_y < 10:
                tx_rgba = tex.pixels[i_x, i_y] * np.array(
                    [10, 10, 10, 1], dtype=np.uint8
                )
        display.pixels[y, x, :3] = tx_rgba[:3]

    display[:, :, :3] = display.pixels[:, :, :3]
    {
        "color": lambda x: Printer().print(x.pixels),
        "python": lambda x: pyprint(x.scan_data(), "display"),
    }.get(mode)(display)


def pyprint(thing, name):
    print(
        f"""
{name} = {repr(thing)}
"""
    )


class AssetMaterialiser:
    assets = {
        "open_ground": gen_open_ground(),
        "rock": gen_rock(),
        "split_rock": gen_split_rock(),
        "spike": gen_spike(),
        "ice_pillars": gen_ice_pillars(),
        "short_pillar": gen_short_cactus(),
        "tall_pillar": gen_tall_cactus(),
        "reeds": gen_reeds(),
        "brown_shrub": gen_brown_shrub(),
        "green_shrub": gen_green_shrub(),
        "yellow_shrub": gen_yellow_shrub(),
    }

    import_strings = [
        "from numpy import array, uint8\n",
        "from typing import NamedTuple\n\n",
    ]

    class_string = "class MaterialisedAssets(NamedTuple):\n"

    def assignment_string(thing: bytearray, name: str) -> str:
        return f"""\t{name} = {repr(thing)}\n"""

    def materialise():
        with open("./assets/materialised_assets.py", "w") as file:
            for string in AssetMaterialiser.import_strings:
                file.write(string)
            file.write(AssetMaterialiser.class_string)

            for name, asset in AssetMaterialiser.assets.items():
                file.write(AssetMaterialiser.assignment_string(asset.scan_data(), name))
