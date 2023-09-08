from typing import Generator, NamedTuple, Self

import arcade
import PIL.Image
from pyglet.math import Vec2, Vec4


class RGBA(NamedTuple):
    R: int = 0
    G: int = 0
    B: int = 0
    A: int = 0

    def __add__(self, other: Self) -> Self:
        return RGBA(*(Vec4(*self) + Vec4(*other)))

    def __mul__(self, other: int | float) -> Self:
        return RGBA(*(Vec4(*self) * other))

    def is_valid(self) -> bool:
        return max(*self) < 256


def gradient(start: RGBA, step: RGBA) -> Generator[RGBA, None, None]:
    current = start
    while current.is_valid():
        yield current
        current = current + step


def iter_px(size: tuple[int, int]) -> Generator[tuple[int, int], None, None]:
    w, h = size
    for y in reversed(range(h)):
        for x in range(w):
            yield x, y


class Gradient(NamedTuple):
    start: RGBA = RGBA()
    step: RGBA = RGBA()
    initial: Vec2 = Vec2()
    direction: Vec2 = Vec2(1, 0)

    def sample(self, x: int, y: int) -> RGBA:
        displacement = Vec2(x, y) - self.initial
        norm_dir = self.direction.normalize()
        step_count = round(displacement.dot(norm_dir) / self.direction.mag)
        return self.start + self.step * int(step_count)


def flat_map(image, grad: Gradient):
    height_map = PIL.Image.new("RGBA", image.size, color=(0, 0, 0, 0))
    for px in iter_px(image.size):
        src_px = RGBA(*image.getpixel(px))
        if src_px.A <= 0:
            continue
        height_map.putpixel(px, grad.sample(*px))
    return height_map


def flat_normal_map(texture: arcade.Texture) -> arcade.Texture:
    image = texture.image
    normal_map = flat_map(image, Gradient(start=RGBA(R=255, G=255, A=255)))

    return arcade.Texture(normal_map, hit_box_points=texture.hit_box_points)


def flat_sprite_height_map(texture: arcade.Texture):
    image = texture.image
    grad = Gradient(
        start=RGBA(A=255),
        step=RGBA(R=1, G=1, B=1),
        initial=Vec2(0, image.height),
        direction=Vec2(0, -1),
    )
    height_map = flat_map(image, grad)

    return arcade.Texture(height_map, hit_box_points=texture.hit_box_points)
