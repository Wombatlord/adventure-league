from typing import Optional

import arcade
from arcade.gui import NinePatchTexture


class PixelatedNinePatch(NinePatchTexture):
    def __init__(
        self,
        left: int | None = None,
        right: int | None = None,
        bottom: int | None = None,
        top: int | None = None,
        texture: arcade.Texture | None = None,
        atlas: Optional[arcade.TextureAtlas] = None,
    ):
        try:
            super().__init__(
                left=left,
                right=right,
                bottom=bottom,
                top=top,
                texture=texture,
                atlas=atlas,
            )
        except Exception as e:
            raise ValueError(
                "You forgot to supply one of the required arguments to construct a PixelatedNinePatch."
            ) from e

    # Preserve the docstring from the super class.
    __init__.__doc__ = NinePatchTexture.__doc__

    def draw_sized(
        self,
        *,
        position: tuple[float, float] = (0, 0),
        size: tuple[float, float],
    ):
        super().draw_sized(position=position, size=size, pixelated=True)
