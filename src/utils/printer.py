import numpy as np


class Printer:
    ESC = "\x1B"
    CSI = f"{ESC}["

    @classmethod
    def paint(cls, s: str, r: int, g: int, b: int) -> str:
        return "".join(
            [
                f"{cls.CSI}38;2;{r};{g};{b}m",
                s,
                f"{cls.CSI}0m",
            ]
        )

    def __init__(self):
        pass

    def apply_rgb(self, s: str, rgba: np.array):
        *rgb, a = tuple(rgba)
        if a < 200:
            return " " * 2
        else:
            return self.paint(s, *rgb)

    def print(self, image: np.array):
        print("\t" + "".join(f"{x:>#2d}" for x in range(image.shape[1])))
        for i, row in enumerate(image):
            print(f"{i=}", end="\t")
            for rgba in row:
                print(self.apply_rgb("█" * 2, rgba), end="")
            print("")
