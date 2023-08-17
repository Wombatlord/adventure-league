from typing import Callable, Generator

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from src.textures.texture_data import SpriteSheetSpecs

source_tx = SpriteSheetSpecs.tile_normals_2_layer.loaded[0]

Point = tuple[int, int]
RGBA = tuple[int, int, int, int]
HeightMapper = Callable[[RGBA], RGBA]
Predicate = Callable[[RGBA], bool]


def iter_up_cols(w, h) -> Generator[Generator[Point, None, None], None, None]:
    x_px, y_px = [*range(w)], [*range(h)]
    for x in x_px:
        yield ((x, y) for y in y_px[::-1])


def height_mapper(base_height: int, max_height: int):
    rgba = lambda h: (h, h, h, 255)
    h_range = [*range(base_height, max_height)]
    colours = [rgba(y) for y in h_range]
    final = rgba(max_height)

    def mapper(incoming: RGBA) -> RGBA:
        nonlocal colours
        r, g, b, a = incoming
        if a == 0:
            return incoming

        if b:
            return final

        if colours:
            colour = colours.pop(0)
        else:
            colour = final
        return colour

    return mapper


def gen_height_map_tile(base_height: int, delta: int, src: Image) -> Image.Image:
    dst = src.copy()
    for column in iter_up_cols(*src.size):
        mapper = height_mapper(base_height, base_height + delta)
        for xy in column:
            dst.putpixel(xy, mapper(src.getpixel(xy)))

    return dst


def generate_height_map_sheet() -> Image.Image:
    img: Image.Image | None = None
    for base_height in range(0, 255 - 8, 8):
        tile = gen_height_map_tile(base_height, 9, source_tx.image)
        if not img:
            img = tile
            continue

        next_img = Image.new("RGBA", (img.width, img.height + tile.height))
        next_img.paste(img, (0, 0))
        next_img.paste(tile, (0, img.height))
        img = next_img

    return img


def generate(path: str = SpriteSheetSpecs.tile_height_map_sheet.args[0]):
    result = generate_height_map_sheet()
    metadata = PngInfo()
    result.save(path, format="PNG", pnginfo=metadata)
