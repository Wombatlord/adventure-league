import numpy as np
from typing import Generator


def rgba(r: int, g: int, b: int, a: int) -> np.array:
    return np.array([r, g, b, a], dtype=np.uint8)

def grey(g: int):
    return rgba(g, g, g, g)


class DataTexture:
    pixels: np.array

    def __init__(self, size: tuple[int, int], dtype=np.uint8):
        self.pixels = np.zeros(size + (4,), dtype=dtype)
        
    def __getitem__(self, *indices):
        if len(indices) >= 2:
            indices = indices[:2][::-1] + indices[2:]
        return self.pixels.__getitem__(*indices)

    def scanner(self) -> Generator[np.array, None, None]:
        for y in range(self.pixels.shape[1]):
            for x in range(self.pixels.shape[2]):
                yield self.pixels[x, y]

    def scan_data(self) -> bytearray:
        buffer = bytearray()
        for rgba in self.scanner():
            buffer.extend(rgba)

        return buffer
    

height_map = DataTexture((10, 10), dtype=np.uint8)
ground = grey(8)
pillar = grey(16)
height_map.pixels[:, :] = ground
border=3
height_map.pixels[border:-border, border:-border] = pillar

print(height_map[:, :, 0])