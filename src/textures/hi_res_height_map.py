from __future__ import annotations

from typing import Generator, NamedTuple, Sequence, TypeVar

import numpy as np
from skimage import io, util

from src.textures.texture_data import SingleTextureSpecs
from src.utils.printer import Printer

CHANNEL_MIN = 0
CHANNEL_MAX = (1 << 16) - 1
STEP = 16


def generate_height_map(path: str = SingleTextureSpecs.tile_normals_hi_res.args[0]):
    image = util.img_as_uint(io.imread(path))


class Pt(NamedTuple):
    x: int = 0
    y: int = 0

    def __mul__(self, factor: float | int) -> Pt:
        return Pt(factor * self.x, factor * self.y)

    __rmul__ = __mul__

    def __add__(self, other: int | float | Pt | tuple[int | float, int | float]) -> Pt:
        if isinstance(other, (int, float)):
            dx, dy = other, other
        else:
            dx, dy = other

        x, y = self

        return Pt(
            x + dx,
            y + dy,
        )

    __radd__ = __add__

    def __neg__(self) -> Pt:
        return -1 * self

    def __sub__(self, other: Pt | int | float | tuple[int | float, int | float]) -> Pt:
        minus_other = -other
        result = self + minus_other
        return result


vertices = lambda w, h: (
    # Top diamond shape
    Pt(0, h // 4),
    Pt(w // 2, 0),
    Pt(w, h // 4),
    Pt(w // 2, h // 2),  # closest point to viewer
    # Three visible lower vertices
    Pt(0, 3 * h // 4),
    Pt(w // 2, h),  # lowest vertex
    Pt(w, 3 * h // 4),
)


def cycle(n, offset=0):
    signal = offset
    while True:
        yield signal
        signal = (signal + 1) % n


_T = TypeVar("_T", bound=object)


def loop_forever(items: Sequence[_T], offset=0) -> Generator[_T, None, None]:
    yield from (items[idx] for idx in cycle(len(items), offset))


max_lengths = [64, 64, 65]


class Path:
    steps: tuple[Pt, ...]
    bounds: Pt
    length: int

    def __init__(self, steps: tuple[Pt, ...], bounds: Pt):
        self.steps = steps
        self.length = 0
        self.bounds = bounds
        print(f"{self.bounds=}")

    def start_from(self, pt: Pt, max_len=64, offset=0) -> Generator[Pt, None, None]:
        current = pt
        self.length = 1
        for step in loop_forever(self.steps, offset):
            if 0 > current.x or current.x >= self.bounds.x:
                break
            if 0 > current.y or current.y >= self.bounds.y:
                break
            if self.length > max_len:
                break
            yield current
            current += step
            self.length += 1

    @classmethod
    def parallel_to_x(cls, bounds: Pt) -> Path:
        return cls(
            steps=(Pt(1, 0), Pt(1, -1)),
            bounds=bounds,
        )

    @classmethod
    def parallel_to_y(cls, bounds: Pt) -> Path:
        return cls(
            steps=(Pt(-1, 0), Pt(-1, -1)),
            bounds=bounds,
        )

    @classmethod
    def parallel_to_z(cls, bounds: Pt) -> Path:
        return cls(
            steps=(Pt(0, -1),),
            bounds=bounds,
        )


class Parallels(NamedTuple):
    x: Path
    y: Path
    z: Path

    @classmethod
    def create(cls, bounds):
        return cls(
            x=Path.parallel_to_x(bounds),
            y=Path.parallel_to_y(bounds),
            z=Path.parallel_to_z(bounds),
        )

    @property
    def position(self) -> tuple[int, int, int]:
        return (
            self.x.length,
            self.y.length,
            self.z.length,
        )

    def iter_plane_normal(
        self, plane_idx: int, start: Pt, plane_offset=0
    ) -> Generator[Pt, None, None]:
        if plane_idx < 0 or plane_idx >= 3:
            raise ValueError(f"Plane idx must be 0, 1 or 2. Got {plane_idx=}")

        self[plane_idx].length = plane_offset

        px_gen, row_gen, *_ = [p for i, p in enumerate(self) if i != plane_idx]

        row_offset, px_offset = [
            (0, 0),
            (0, 0),
            (0, 0),
        ][plane_idx]

        max_cols, max_rows = [
            (64, 65),
            (64, 65),
            (64, 64),
        ][plane_idx]

        for start in row_gen.start_from(start, offset=row_offset, max_len=max_cols):
            for point in px_gen.start_from(start, offset=px_offset, max_len=max_rows):
                yield point


def modify(source: np.array, dst: np.array) -> np.array:
    corners = tuple(c + Pt(0, 0) for c in vertices(*([source.shape[1]] * 2)))
    (top_left, top_back, top_right, top_front, btm_left, btm_front, btm_right) = corners
    bounds = Pt(source.shape[1], source.shape[0])
    parallels = Parallels.create(bounds)
    plane(parallels, 0, btm_front, source, dst)
    plane(parallels, 1, btm_front + Pt(1, 0), source, dst)
    plane(parallels, 2, top_front + Pt(1, -1), source, dst)
    plane(parallels, 2, top_front + Pt(0, -1), source, dst)


def plane(
    parallels: Parallels, normal_idx: int, origin: Pt, src: np.array, dst: np.array
):
    plane_offset = 0
    if normal_idx == 2:
        plane_offset = 64

    for px, py in parallels.iter_plane_normal(normal_idx, origin, plane_offset):
        if src[py, px, normal_idx] < 200:
            print(f"SKIPPING {(px, py, normal_idx)=} with {src[py, px, normal_idx]=}")
            continue
        rgb = map(lambda x: 2 * x, parallels.position)
        dst[py, px] = [*rgb, 255]


def test(path: str = SingleTextureSpecs.tile_normals_hi_res.args[0]):
    image = io.imread(path)
    dst = np.zeros(image.shape, dtype=np.ubyte)
    modify(image, dst)

    io.imsave("./test.png", dst)
    Printer().print(dst)


def swap_rg(path: str = SingleTextureSpecs.tile_normals_hi_res.args[0]):
    image = io.imread(path)
    dst = np.zeros(image.shape, dtype=np.ubyte)
    is_red = image[:, :, 0] > 200
    is_green = image[:, :, 1] > 200
    is_blue = image[:, :, 2] > 200

    dst[is_red, :] = [0, 255, 0, 255]
    dst[is_green, :] = [255, 0, 0, 255]
    dst[is_blue, :] = [0, 0, 255, 255]
    Printer().print(dst)

    io.imsave("./test.png", dst)


if __name__ == "__main__":
    test()
