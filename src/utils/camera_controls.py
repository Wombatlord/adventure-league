import arcade
from pyglet.math import Vec2

from src.utils.rectangle import Rectangle
from src.world.isometry.transforms import Transform
from src.world.node import Node


class CameraController:
    _camera: arcade.Camera
    _pan_speed: float
    _zoom_increment: float
    _pressed_keys: set[int]
    _v_pan: set[int] = {
        arcade.key.W,
        arcade.key.S,
    }
    _h_pan: set[int] = {
        arcade.key.D,
        arcade.key.A,
    }
    _zoom: set[int] = {
        arcade.key.Q,
        arcade.key.E,
    }

    def __init__(self, camera: arcade.Camera, pan_speed=2.0, zoom_increment=0.002):
        self._camera = camera
        self._pan_speed = pan_speed
        self._zoom_increment = zoom_increment
        self._pressed_keys = set()

    @property
    def listened_keys(self) -> set[int]:
        return self._v_pan | self._h_pan | self._zoom

    def on_key_press(self, key: int) -> int | None:
        include = {key} & self.listened_keys
        self._pressed_keys |= include
        if not include:
            return key

    def on_key_release(self, key) -> int | None:
        include = {key} & self.listened_keys
        self._pressed_keys -= include
        if not include:
            return key

    @property
    def zoom_factor(self) -> float:
        z = 1
        match [*(self._zoom & self._pressed_keys)]:
            case [arcade.key.Q]:
                z += self._zoom_increment
            case [arcade.key.E]:
                z -= self._zoom_increment
            case _:
                pass

        return z

    @property
    def pan_vec(self) -> Vec2:
        l, r, b, t = self._camera.projection
        w, h = r - l, t - b

        u, v = Vec2(w / 2, 0), Vec2(0, h / 2)
        match [*(self._pressed_keys & self._h_pan)]:
            # Right
            case [arcade.key.D]:
                x = 1
            # Left
            case [arcade.key.A]:
                x = -1
            # Both pressed or neither
            case _:
                x = 0

        match [*(self._pressed_keys & self._v_pan)]:
            # Up
            case [arcade.key.W]:
                y = 1
            # Down
            case [arcade.key.S]:
                y = -1
            # Both pressed or neither
            case _:
                y = 0

        return (u * x + v * y).normalize()

    def imaged_rect(self) -> Rectangle:
        return (
            Rectangle.from_projection(*self._camera.projection)
            .translate(self._camera.position)
            .scale_isotropic(self._camera.zoom, fixed_point=self._camera.position)
        )

    def image_px(self, screen_px: Vec2) -> Vec2:
        """Turns the position in terms of viewport pixels into a position in terms of the pixels of the projection"""
        return self.imaged_rect().lerp(
            Rectangle.from_viewport(self._camera.viewport).affine_coords(screen_px),
            translate=True,
        )

    def screen_px(self, image_px: Vec2) -> Vec2:
        """Turns the position in terms of the projection coordinates into a position in terms of viewport pixels"""
        return Rectangle.from_viewport(self._camera.viewport).lerp(
            self.imaged_rect().affine_coords(image_px), translate=True
        )

    def on_update(self):
        self._camera.zoom *= self.zoom_factor
        self._camera.move(self._camera.position + self.pan_vec * self._pan_speed)

    def look_at_world(
        self, position: Node, transform: Transform, distance_per_frame: float = 1
    ):
        """Tell the camera controls to center the view on the world position supplied, maintaining the current zoom level"""
        self._camera.center(transform.project(position), speed=distance_per_frame)

    def __repr__(self):
        cam_pos = f"x={self._camera.position.x:.1f}, y={self._camera.position.y:.1f}"
        return "\n".join([f"{cam_pos=}", f"{self._camera.zoom=}"])
