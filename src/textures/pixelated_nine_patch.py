from typing import Optional

import arcade
from arcade.gui import NinePatchTexture
from arcade.texture import ImageData, Texture
from PIL import Image


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
        **kwargs,
    ):
        super().draw_sized(position=position, size=size, pixelated=True)


class PixelatedTexture(Texture):
    def __init__(
        self,
        image: ImageData,
        *,
        hit_box_algorithm=None,
        hit_box_points=None,
        hash: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(image=image, **kwargs)

    __init__.__doc__ = Texture.__doc__

    def draw_sized(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        angle: float = 0.0,
        alpha: int = 255,
    ):
        """
        Draw a texture with a specific width and height.

        .. warning:: This is a very slow method of drawing a texture,
                     and should be used sparingly. The method simply
                     creates a sprite internally and draws it.

        :param float center_x: X position to draw texture
        :param float center_y: Y position to draw texture
        :param float width: Width to draw texture
        :param float height: Height to draw texture
        :param float angle: Angle to draw texture
        :param int alpha: Alpha value to draw texture
        """
        from arcade import Sprite

        spritelist = self._create_cached_spritelist()
        sprite = Sprite(
            self,
            center_x=center_x,
            center_y=center_y,
            angle=angle,
        )
        # sprite.size = (width, height)
        sprite.width = width
        sprite.height = height

        sprite.alpha = alpha
        # Due to circular references we can't keep the sprite around
        spritelist.append(sprite)
        spritelist.draw(pixelated=True)
        spritelist.remove(sprite)
