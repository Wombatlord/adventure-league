from typing import Any

from arcade.gui import NinePatchTexture


class PixelatedNinePatch(NinePatchTexture):
    def draw_sized(
        self,
        *,
        position: tuple[float, float] = (0, 0),
        size: tuple[float, float],
    ):
        super().draw_sized(position=position, size=size, pixelated=True)


def get_pixelated_nine_patch(
    texture_button_nine_patch_config: dict[str, Any],
) -> tuple[PixelatedNinePatch, PixelatedNinePatch, PixelatedNinePatch]:
    np = texture_button_nine_patch_config["nine_patch"]
    main_tex = np(**texture_button_nine_patch_config["main_tex"])
    pressed_tex = np(**texture_button_nine_patch_config["pressed_tex"])
    hovered_tex = np(**texture_button_nine_patch_config["hovered_tex"])

    return (main_tex, pressed_tex, hovered_tex)
