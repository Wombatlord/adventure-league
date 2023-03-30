from arcade.gui import NinePatchTexture


class PixelatedNinePatch(NinePatchTexture):
    def draw_sized(
        self,
        *,
        position: tuple[float, float] = (0, 0),
        size: tuple[float, float],
    ):
        super().draw_sized(position=position, size=size, pixelated=True)
