import operator

from pyglet.math import Mat3, Vec2, Vec3, Mat4

from src.utils.pathing.grid_utils import Node


class Transform:
    _world_to_screen: Mat3
    _screen_to_world: Mat3

    def __init__(self, block_dimensions: tuple[int, int, int] | Vec3, absolute_scale: float):
        """
        Here's a pic to show how to measure block dimensions from a cube sprite:


                                      block_dimensions[0]
                              <------------------------------------>
                                           ___------___               ^
                                     ___---            ---___         |
                               ___---                        ---___   | block_dimensions[1]
                           ^   |  ---___                  ___---  |   |
                           |   |        ---___      ___---        |   v
                           |   |              ------              |
        block_dimensions[2]|   |                 |                |
                           |   |                 |                |
                           |   |                 |                |
                           |   |                 |                |
                           v   |__               |              __|
                                  ---___         |        ___---
                                        ---___   |  ___---
                                              ---|--


        Args:
            block_dimensions: the isometric block dimensions in SOURCE TEXTURE PIXELS in the following order
            0. corner to corner horizontal pixel width of the flat upper surface of the block
            1. corner to corner vertical pixel width of the flat upper surface of the block
            2. side height (z-height) in pixels of the block
            absolute_scale: this is the scale you supply to the sprite instantiation.
        """
        # This matrix is just trivial transformation * some scale (call it s)
        # i.e. (x, y, z) -> (s * x, s * y, s * z) = s * (x, y, z)
        # this should be the only part that does not preserve the volume
        scale_transform = Mat3(absolute_scale * element for element in Mat3())

        # grid is the half block translation vector
        grid = Vec3(*block_dimensions) / 2

        # This matrix takes care of the entire isometric transform including any aspect ratio changes
        isometry = Mat3([
            # c1     c2                 c3       <-column labels
            -grid.x, +grid.y,           0.0,    # c1 expresses the fact that screen x = world y - world x
            +grid.x, +grid.y,           0.0,    # c2 expresses the fact that screen y = world x + world y + 2*world z
             0.0,    +grid.z+grid.y,    1.0,    # c3 expresses the fact that we don't care about screen z
        ])

                                # the determinant so that it preserves volumes

        self._world_to_screen = (   # The order of operations (bottom to top) T3(T2(T1(v))
            scale_transform @       # 3. apply absolute scaling
            isometry                # 1. map to a flat isometric grid where the "tiles"
        )

        # pyglet Mat3 type can't be inverted to get the screen -> world matrix so we need to embed it in a
        # Mat4 to make use of their implementation of Mat4.__invert__
        embedded = self._world_to_screen
        invertible_w2s = _embed_mat3_in_mat4(embedded)

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

        # here we grab the x and y parts to locate the grid point on the screen
        screen_xy_projection = screen_xyz[:2]
        return Vec2(*screen_xy_projection)

    def to_world(self, cam_coords: Vec2) -> Node:
        embedded = Vec3(*cam_coords)
        return Node(*(self._screen_to_world @ embedded))


def _embed_mat3_in_mat4(embedded: Mat3) -> Mat4:
    return Mat4([
        *embedded[0:3], 0.0,
        *embedded[3:6], 0.0,
        *embedded[6:9], 0.0,
        0.0, 0.0, 0.0,  1.0,
    ])


def mat3_determinant(m3: Mat3) -> float:
    """This implementation is due to pyglet, and wholly cribbed from the implementation of Mat4.__invert__"""
    m = _embed_mat3_in_mat4(m3)
    a = m[10] * m[15] - m[11] * m[14]
    b = m[9] * m[15] - m[11] * m[13]
    c = m[9] * m[14] - m[10] * m[13]
    d = m[8] * m[15] - m[11] * m[12]
    e = m[8] * m[14] - m[10] * m[12]
    f = m[8] * m[13] - m[9] * m[12]

    det = (
        m[0] * (m[5] * a - m[6] * b + m[7] * c) -
        m[1] * (m[4] * a - m[6] * d + m[7] * e) +
        m[2] * (m[4] * b - m[5] * d + m[7] * f) -
        m[3] * (m[4] * c - m[5] * e + m[6] * f)
    )

    return det


def norm(m3: Mat3) -> Mat3:
    """scales any lossless 3d -> 3d transform so that it preserves the volume of transformed shapes"""
    det = mat3_determinant(m3)
    if det == 0:
        raise ValueError("Cannot force a non-invertible (lossy) transform to preserve volume (lossless)")
    scalar = abs(det)**(-1/3)
    uniform_scaling = Mat3((
        scalar, 0.0, 0.0,
        0.0, scalar, 0.0,
        0.0, 0.0, scalar,
    ))

    scale_preserving_transform = uniform_scaling @ m3
    return scale_preserving_transform
