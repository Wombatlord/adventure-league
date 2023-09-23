from typing import Callable, Generator

import numpy as np


def rgba(r: int, g: int, b: int, a: int) -> np.array:
    return np.array([r, g, b, a], dtype=np.uint8)


def grey(g: int):
    return rgba(g, g, g, g)


def clamp(minimum: int) -> Callable[[int], Callable[[int], Callable[[int], int]]]:
    def clamp_to(maximum: int) -> Callable[[int], int]:
        return lambda x: x if x is None else min(maximum - 1, max(minimum, x))

    return clamp_to


class DataTexture:
    pixels: np.array

    def __init__(self, size: tuple[int, int], dtype=np.uint8):
        if isinstance(size, np.ndarray):
            size = tuple(size)
        self.pixels = np.zeros(size + (4,), dtype=dtype)
        self.debug = [lambda *_: None, lambda *_: None]

    def __getitem__(self, *indices):
        (indices,) = indices

        clamps = [clamp(0)(size) for size in self.pixels.shape]
        clamped = []
        for axis, idx in enumerate(indices):
            clump = clamps[axis]
            if isinstance(idx, slice):
                idx = slice(clump(idx.start), clump(idx.stop), idx.step)
            elif isinstance(idx, (int, np.signedinteger)):
                idx = clump(idx)
            else:
                pass
            clamped.append(idx)
        indices = tuple(clamped)
        if len(indices) >= 2:
            indices = indices[:2][::-1] + indices[2:]

        if len(indices) == 3:
            x, y, z = indices
            return self.pixels[x, y, z]
        elif len(indices) == 2:
            x, y = indices
            return self.pixels[x, y]
        else:
            return self.pixels[x]
        return self.pixels.__getitem__((indices,))

    def __setitem__(self, *args):
        indices, value = args
        clamps = [clamp(0)(size) for size in self.pixels.shape]
        indices = [
            clamp(idx) if type(idx) is not slice else idx
            for clamp, idx in zip(clamps, indices)
        ]

        match indices:
            case x, y, z if x and y and z:
                self.pixels[y, x, z] = value
            case x, y if x and y:
                self.pixels[y, x] = value
            case x, if x:
                self.pixels[:, x] = value

    def scanner(self) -> Generator[np.array, None, None]:
        for y in range(self.pixels.shape[0]):
            for x in range(self.pixels.shape[1]):
                yield self.pixels[x, y]

    def scan_data(self) -> bytearray:
        buffer = bytearray()
        for rgba in self.scanner():
            buffer.extend(rgba)

        return buffer


height_map = DataTexture((10, 10), dtype=np.uint8)
