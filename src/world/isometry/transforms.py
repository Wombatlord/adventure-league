import math
from typing import Self

from pyglet.math import Mat3, Mat4, Vec2, Vec3, Vec4

from src.world.node import Node


class Transform:
    _world_to_screen: Mat4
    _screen_to_world: Mat4

    @classmethod
    def trivial(cls) -> Self:
        return cls()

    def __init__(self, world_to_screen: Mat4 = Mat4(), translation: Vec2 = Vec2()):
        self._set(world_to_screen)
        self.translate_image(translation)

    def on_resize(self, translation: Vec2):
        self.translate_image(translation)

    @classmethod
    def isometric(cls, block_dimensions: tuple[int, int, int] | Vec3, absolute_scale: float, translation: Vec2 = Vec2()):
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
            translation: this is the shift to wherever the image should appear on screen.
        """
        # This matrix is just trivial transformation * some scale (call it s)
        # i.e. (x, y, z) -> (s * x, s * y, s * z) = s * (x, y, z)
        # this should be the only part that does not preserve the volume
        scale_transform = Mat3(absolute_scale * element for element in Mat3())

        # grid is the half block translation vector
        grid = Vec3(*block_dimensions) / 2

        # This matrix takes care of the entire isometric transform including any aspect ratio changes
        cam_basis = Vec3(
            Vec3(grid.x, -grid.x, 0), # screen right
            Vec3(grid.y, grid.y, 2*grid.y), # screen up
            Vec3(0, 0, 2*grid.z), #screen out
        )
        cx, cy, cz = cam_basis

        isometry = Mat3([
            cx.x, cy.x, cz.x,    # cx expresses the fact that screen x = world y - world x
            cx.y, cy.y, cz.y,    # cy expresses the fact that screen y = world x + world y + 2*world z
            cx.z, cy.z, cz.z,    # cz expresses the fact that we don't care about screen z
        ])
                                # the determinant so that it preserves volumes

        world_to_screen = (   # The order of operations (bottom to top) T2(T1(v))
            scale_transform @       # 2. apply absolute scaling
            isometry                # 1. map to an isometric grid projection
        )

        # pyglet Mat3 type can't be inverted to get the screen -> world matrix so we need to embed it in a
        # Mat4 to make use of their implementation of Mat4.__invert__
        transform = cls(_embed_mat3_in_mat4(world_to_screen), translation=translation)
        return transform
    
    def _set(self, wts: Mat4):
        self._world_to_screen = wts
        self._screen_to_world = ~self._world_to_screen
    
    def translate_image(self, translation: Vec2):
        self._set(Mat4().translate(Vec3(*translation, 0)) @ self._world_to_screen)
        
    def translate_grid(self, node: Node):        
        self._set(self._world_to_screen @ Mat4().translate(Vec3(*node)))
        
    def rotate_grid(self, angle: float, pivot_point: Vec2 = Vec2(0, 0)):
        self.translate_grid(pivot_point)
        transform = Mat4().rotate(angle, Vec3(0, 0, 1))
        self._set(self._world_to_screen @ transform)
        self.translate_grid(pivot_point*-1)

    def project(self, node: Node, z_offset: int = 0) -> Vec2:
        # Make sure the input has enough axes and is compatible with matmul (@)
        world_xyzw = Vec4(*(node + Node(0, 0, z=z_offset)), 1)

        # apply our transform
        screen_xyzw = (self._world_to_screen @ world_xyzw)

        # here we grab the x and y parts to locate the grid point on the screen
        screen_xy_projection = screen_xyzw[:2]
        return Vec2(*screen_xy_projection)
    
    def camera_z_axis(self) -> Vec3:
        cam_z = Vec3(*self._screen_to_world.column(2)[:-1])
        return cam_z
    
    def camera_x_axis(self) -> Vec3:
        cam_x = Vec3(*self._screen_to_world.column(0)[:-1])
        return cam_x
    
    def camera_y_axis(self) -> Vec3:
        cam_y = Vec3(*self._screen_to_world.column(1)[:-1])
        return cam_y
    
    def draw_priority(self, node: Node) -> float:
        return 10*self.camera_z_axis().dot(Vec3(*node))

    def world_location(self, cam_xy: Vec2, z: float | int = 0) -> Node:
        """We cast a ray"""
        screen_location = Vec4(*cam_xy, z, 1)
        
        node = Node(*[math.ceil(coord) for coord in (self._screen_to_world @ screen_location)[:3]])
        
        return node

    def screen_to_world(self) -> Mat4:
        return self._screen_to_world
    
    def camera_origin(self) -> Vec3:
        return self.world_location(Vec2(0, 0), 0)

    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, Transform):
            return False

        same_matrix = self._world_to_screen == other._world_to_screen

        return same_matrix

    def is_trivial(self):
        return self == Transform.trivial()

    def clone(self) -> Self:
        return Transform(self._world_to_screen)

def _embed_mat3_in_mat4(embedded: Mat3) -> Mat4:
    return Mat4([
        *embedded[0:3], 0.0,
        *embedded[3:6], 0.0,
        *embedded[6:9], 0.0,
        0.0, 0.0, 0.0,  1.0,
    ])


def _extract_mat3_from_mat4(m4: Mat4) -> Mat3:
    return Mat3([
        *m4[0:3],  # first three of the first row
        *m4[4:7],  # first three of the second row
        *m4[8:11],  # first three of the third row
    ])



def invert_mat3(m3: Mat3) -> Mat3:
    """
    Takes a Mat3 type and returns its inverse as a mat3 if possible
    Args:
        m3: the matrix to invert

    Returns: the inverted matrix
Mat4().rotate(90 * times_90, Vec3(0, 0, 1))
    """
    m4 = _embed_mat3_in_mat4(m3)
    return _extract_mat3_from_mat4(~m4)


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


def draw_priority(node) -> float:
    node_v = Vec3(*node)
    ray = Vec3(-1, -1, 2)
    return node_v.dot(ray)
    
