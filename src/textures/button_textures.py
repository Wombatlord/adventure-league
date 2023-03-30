from typing import Any

from src.textures.pixelated_nine_patch import PixelatedNinePatch


def get_texture_button_textures(
    texture_button_nine_patch_config: dict[str, Any],
) -> tuple[PixelatedNinePatch, PixelatedNinePatch, PixelatedNinePatch]:
    np = texture_button_nine_patch_config["nine_patch"]
    main_tex = np(**texture_button_nine_patch_config["main_tex"])
    pressed_tex = np(**texture_button_nine_patch_config["pressed_tex"])
    hovered_tex = np(**texture_button_nine_patch_config["hovered_tex"])

    return (main_tex, pressed_tex, hovered_tex)
