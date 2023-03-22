import operator

from pyglet.math import Mat3, Vec2, Vec3, Mat4

from src.utils.pathing.grid_utils import Node


class Transform:
    _world_to_screen: Mat3
    _screen_to_world: Mat3

    def __init__(self, aspect_pixels: tuple[int, int], absolute_scale: float):
        # This matrix is just trivial transformation * some scale (call it s)
        # i.e. (x, y, z) -> (s * x, s * y, s * z) = s * (x, y, z)
        scale_transform = Mat3(absolute_scale * element for element in Mat3())

        # this takes care of the relative spacing of nodes so supplying a ratio of (2, 1) is the same
        # as (100, 50). For absolute scaling use the absolute_scale param.
        # The tuple should be thought of as the height and width in pixels of a COMPLETELY FLAT (no world z depth)
        # isometric tile sprite
        asp_x, asp_y = aspect_pixels
        ratio = asp_x / asp_y
        aspect_transform = Mat3([
            ratio, 0.0, 0.0,
            0.0,   1.0, 0.0,
            0.0,   0.0, 1.0
        ])

        # This matrix takes care of the rotation of the grid to the diamond layout
        isometry = Mat3([
            # screen x = world x - world y
            # i.e. right on screen is diagonal in (1, -1) direction in the world
            -1.0, +1.0, 0.0,

            # screen y = world x + world y + 2 * world z
            # i.e. up on screen is diagonal in (1, 1) direction or up (z=1) direction in world
            +1.0, +1.0, 0.0,

            # for making the inverse transform more convenient, we just say screen z = world z
            # there is no screen z so this is ok, because we drop the z coord before returning screen coords
            0.0, +2.0, 1.0,
        ])

        self._world_to_screen = (       # The order of operations (bottom to top) T3(T2(T1(v))
                scale_transform @       # 3. apply absolute scaling
                aspect_transform @      # 2. apply the aspect ratio of the sprites to use
                isometry                # 1. map to a flat isometric grid where the "tiles"
        )                               #    are the same width and height

        # pyglet Mat3 type can't be inverted to get the screen -> world matrix so we need to embed it in a
        # Mat4 to make use of their implementation of Mat4.__invert__
        invertible_w2s = Mat4([
            *self._world_to_screen[0:3], 0.0,
            *self._world_to_screen[3:6], 0.0,
            *self._world_to_screen[6:9], 0.0,
            0.0, 0.0, 0.0,               1.0,
        ])
        # this is the actual inversion
        inverted = ~invertible_w2s

        # here we pull the top-left 3x3 grid out of the inverted 4x4 matrix
        self._screen_to_world = Mat3([
            *inverted[0:3],     # first three of the first row
            *inverted[4:7],     # first three of the second row
            *inverted[8:11],    # first three of the third row
        ])

    def to_screen(self, node: Node) -> Vec2:
        # Make sure the input has enough axes and is compatible with matmul (@)
        world_xyz = Vec3(*node)

        # apply our transform
        screen_xyz = (self._world_to_screen @ world_xyz)

        #
        screen_xy_projection = screen_xyz[:2]
        return Vec2(*screen_xy_projection)

    def to_world(self, cam_coords: Vec2) -> Node:
        embedded = Vec3(*cam_coords)
        return Node(*(self._screen_to_world @ embedded))
