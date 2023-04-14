import math

from pyglet.math import Vec2


def maintain_position(v1: Vec2 | tuple, v2: Vec2 | tuple, thing) -> Vec2:
    if isinstance(v1, tuple):
        v1 = Vec2(v1[0], v1[1])

    if isinstance(v2, tuple):
        v2 = Vec2(v2[0], v2[1])

    current_vec = Vec2(math.sqrt(v1.x**2), math.sqrt(v1.y**2))
    new_vec = Vec2(math.sqrt(v2.x**2), math.sqrt(v2.y**2))

    scale_factor_x = new_vec.x / current_vec.x
    scale_factor_y = new_vec.y / current_vec.y

    thing.x = thing.x * scale_factor_x
    thing.y = thing.y * scale_factor_y

    return Vec2(thing.x, thing.y)
