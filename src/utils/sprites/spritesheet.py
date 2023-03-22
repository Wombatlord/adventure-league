from pathlib import Path

import PIL.Image
from arcade import Texture
from arcade.hitbox import HitBoxAlgorithm
from arcade.resources import resolve_resource_path


def load_spritesheet(
    file_name: str | Path,
    sprite_width: int,
    sprite_height: int,
    columns: int,
    count: int,
    top_left_offset: int | tuple[int, int] = 0,
    hit_box_algorithm: HitBoxAlgorithm | None = None,
) -> list[Texture]:
    """
    :param str file_name: Name of the file to that holds the texture.
    :param int sprite_width: Width of the sprites in pixels
    :param int sprite_height: Height of the sprites in pixels
    :param int columns: Number of tiles wide the image is.
    :param int count: Number of tiles in the image.
    :param int top_left_offset: the top left corner of the sprites relative to the grid
    :param str hit_box_algorithm: The hit box algorithm
    :returns List: List of :class:`Texture` objects.
    """
    texture_list = []
    if isinstance(top_left_offset, tuple) and len(top_left_offset) == 2:
        margin_x, margin_y = top_left_offset
    else:
        margin_x, margin_y = top_left_offset, top_left_offset

    # TODO: Support caching?
    file_name = resolve_resource_path(file_name)
    source_image = PIL.Image.open(file_name).convert("RGBA")

    for sprite_no in range(count):
        row = sprite_no // columns
        column = sprite_no % columns
        start_x = (sprite_width + margin_x) * column
        start_y = (sprite_height + margin_y) * row
        image = source_image.crop(
            (start_x, start_y, start_x + sprite_width, start_y + sprite_height)
        )
        texture = Texture(
            image,
            hit_box_algorithm=hit_box_algorithm,
        )
        texture.file_path = file_name
        texture.crop_values = start_x, start_y, sprite_width, sprite_height
        texture_list.append(texture)

    return texture_list
