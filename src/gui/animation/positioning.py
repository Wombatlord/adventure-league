import math

from pyglet.math import Vec2


def maintain_position(v1: Vec2 | tuple, v2: Vec2 | tuple, thing) -> Vec2:
    """Calculates the new position of thing relative to a known vector based on scaling.

    Args:
        v1 (Vec2 | tuple): The original vector which the position of thing is relative to, eg Window dimensions pre-resize.
        v2 (Vec2 | tuple): The scaled vector of the original vector, eg New window dimensions after scaling.
        thing (_type_): Something like a UIAnchorLayout which should maintain its position relative to the scaled vector.

    Returns:
        Vec2: The new (x,y) of the thing after the scaling operations.
    """

    if isinstance(v1, tuple):
        v1 = Vec2(v1[0], v1[1])

    if isinstance(v2, tuple):
        v2 = Vec2(v2[0], v2[1])

    # Calculate the scale factor of the x and y components.
    # For example, the scale factor of the vector corresponding to a window resize
    current_vec = Vec2(math.sqrt(v1.x**2), math.sqrt(v1.y**2))
    new_vec = Vec2(math.sqrt(v2.x**2), math.sqrt(v2.y**2))

    scale_factor_x = new_vec.x / current_vec.x
    scale_factor_y = new_vec.y / current_vec.y

    # Set new (x, y) of the thing based on scaled vector.
    # For example, a UIAnchorLayout that should maintain its position relative to the window after scaling the window.
    thing.x = thing.x * scale_factor_x
    thing.y = thing.y * scale_factor_y

    return Vec2(thing.x, thing.y)
