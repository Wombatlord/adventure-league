from pyglet.math import Vec2
import arcade

from src.gui.window_data import WindowData
from src.utils.pathing.grid_utils import Node


def grid_offset(
    x: int,
    y: int,
    window_scale: tuple[float, float],
    tile_base_dims: tuple[int, int],
    scale_factor: float,
    width: int,
    height: int,
) -> Vec2:
    grid_scale = 0.75
    sx, sy = window_scale
    constant_scale = grid_scale * tile_base_dims[0] * scale_factor
    return Vec2(
        (x - y) * sx * 13,
        (x + y) * sy * 5,
    ) * constant_scale + Vec2(width / 2, 7 * height / 8)


def wall_tile_at(
        x: int, y: int, orientation: Node, width, height, scale_factor=1
    ) -> tuple[arcade.Sprite, ...]:
        window_scale = WindowData.scale
        tile_base_dims = (16,17)
        scale = 5 #* scale_factor
        wall = sprite_at(arcade.Sprite(scale=scale), x, y, window_scale, tile_base_dims, scale_factor, width, height)
        if orientation == Node(1, 0):
            # Right / East Walls
            print(wall.center_y)
            wall.center_y += 55
            wall.center_x += 50
            sprites = (wall,)

        elif orientation == Node(1, 1):
            # Three wall sprites for the corner
            left = sprite_at(arcade.Sprite(scale=scale), x, y, window_scale, tile_base_dims, scale_factor, width, height)
            right = sprite_at(arcade.Sprite(scale=scale), x, y, window_scale, tile_base_dims, scale_factor, width, height)
            top = sprite_at(arcade.Sprite(scale=scale), x, y, window_scale, tile_base_dims, scale_factor, width, height)
            left.center_y += 55
            left.center_x -= 50
            right.center_y += 55
            right.center_x += 50
            top_offset = grid_offset(13, 13, window_scale, tile_base_dims, scale_factor, width, height)
            top.center_y = top_offset.y
            sprites = (left, right, top)

        else:
            # Left / West Walls
            wall.center_y += 55
            wall.center_x -= 50
            sprites = (wall,)

        for s in sprites:
            s.texture = WindowData.tiles[89]

        return sprites


def floor_tile_at(
    x: int,
    y: int,
    window_scale,
    tile_base_dims,
    scale_factor,
    width,
    height,
    texture,
    scale=1,
) -> arcade.Sprite:
    tile = arcade.Sprite(scale=5 * scale)
    tile.texture = texture

    return sprite_at(
        tile, x, y, window_scale, tile_base_dims, scale_factor, width, height
    )


def sprite_at(
    sprite: arcade.Sprite,
    x: int,
    y: int,
    window_scale: tuple[float, float],
    tile_base_dims: tuple[int, int],
    scale_factor: float,
    width: int,
    height: int,
) -> arcade.Sprite:
    offset = grid_offset(
        x,
        y,
        window_scale,
        tile_base_dims,
        scale_factor,
        width,
        height,
    )
    sprite.center_x, sprite.center_y = offset
    return sprite
