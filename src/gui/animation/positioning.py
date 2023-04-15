import math

from pyglet.math import Mat3, Vec2, Vec3


def maintain_position(v1: Vec2 | tuple, v2: Vec2 | tuple, thing) -> Vec2:
    """Calculates the new position of thing relative to a known vector based on scaling.

    Args:
        v1 (Vec2 | tuple): The original vector which the position of thing is relative to, eg Window dimensions pre-resize.
        v2 (Vec2 | tuple): The scaled vector of the original vector, eg New window dimensions after scaling.
        thing (_type_): Something like a UIAnchorLayout which should maintain its position relative to the scaled vector.

    Returns:
        Vec2: The new (x,y) of the thing after the scaling operations.
    """
    before_vec = Vec2(*v1)
    after_vec = Vec2(*v2)

    # Calculate the scale factor of the x and y components.
    # For example, the scale factor of the vector corresponding to a window resize
    scale_factor_x = after_vec.x / before_vec.x
    scale_factor_y = after_vec.y / before_vec.y

    # Set new (x, y) of the thing based on scaled vector.
    # For example, a UIAnchorLayout that should maintain its position relative to the window after scaling the window.
    thing.x = thing.x * scale_factor_x
    thing.y = thing.y * scale_factor_y

    return Vec2(thing.x, thing.y)


def mat_maintain_position(v1: Vec2 | tuple, v2: Vec2 | tuple, thing) -> Vec2:
    """Calculates the new position of thing relative to a known vector based on scaling.

    Args:
        v1 (Vec2 | tuple): The original vector which the position of thing is relative to, eg Window dimensions pre-resize.
        v2 (Vec2 | tuple): The scaled vector of the original vector, eg New window dimensions after scaling.
        thing (_type_): Something like a UIAnchorLayout which should maintain its position relative to the scaled vector.

    Returns:
        Vec2: The new (x,y) of the thing after the scaling operations.
    """
    v1, v2 = Vec2(*v1), Vec2(*v2)

    rows = (
        (v2.x / v1.x, 0, 0),
        (0, v2.y / v1.y, 0),
        (0, 0, 0),
    )

    mat = Mat3([*rows[0], *rows[1], *rows[2]])

    v_thing = Vec3(thing.x, thing.y, 0)

    return Vec2(*(mat @ v_thing)[:2])
