import numpy as np
from typing import Generator


def rgba(r: int, g: int, b: int, a: int) -> np.array:
    return np.array([r, g, b, a], dtype=np.uint8)


class DataTexture:
    pixels: np.array

    def __init__(self, size: tuple[int, int], dtype=np.uint8):
        self.pixels = np.zeros(size + (4,), dtype=dtype)

    def scanner(self) -> Generator[np.array, None, None]:
        for y in range(self.pixels.shape[1]):
            for x in range(self.pixels.shape[2]):
                yield self.pixels[x, y]

    def scan_data(self) -> bytearray:
        buffer = bytearray()
        for rgba in self.scanner():
            buffer.extend(rgba)

        return buffer
    

