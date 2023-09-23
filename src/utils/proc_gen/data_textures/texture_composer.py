import numpy as np

from src.utils.printer import Printer
from src.utils.proc_gen.data_textures.data_texture import DataTexture

TILE_X = np.array([9, 0], dtype=int)
TILE_Y = np.array([0, 9], dtype=int)
TILE_SHAPE = TILE_X + TILE_Y
CANVAS_SHAPE = TILE_SHAPE * 3


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

    arr[1:4, 3:6, :3] = short
    arr[5:8, 3:6, :3] = tall

    return dt


def gen_cactus() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    ground = 8
    tall = 16
    dt.pixels[:, :, :3] = ground
    dt.pixels[:, :, 3] = 255
    dt.pixels[3:6, 3:6, :3] = tall

    return dt


def white_square() -> DataTexture:
    dt = DataTexture(TILE_SHAPE)
    dt.pixels[:, :] = [255] * 4
    return dt


def main(*args):
    args = [*args]
    mode = "color"
    if args:
        mode = args.pop(0)

    tex = gen_cactus()
    mapping = {(0, 1): gen_cactus(), (1, 0): gen_ice_pillars(), (1, 1): gen_spike()}

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

            if 0 <= i_x < 9 and 0 <= i_y < 9:
                tx_rgba = tex.pixels[i_x, i_y] * np.array(
                    [10, 10, 10, 1], dtype=np.uint8
                )
        display.pixels[y, x, :3] = tx_rgba[:3]

    display[:, :, :3] = display.pixels[:, :, :3]
    {
        "color": lambda x: Printer().print(x.pixels),
        "python": lambda x: pyprint(x.scan_data()),
    }.get(mode)(display)


def pyprint(thing):
    print(
        f"""
from numpy import array, uint8
data = {repr(thing)}
"""
    )


if __name__ == "__main__":
    import sys

    main(*sys.argv[1:])
