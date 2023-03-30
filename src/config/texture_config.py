from src.textures.pixelated_nine_patch import PixelatedNinePatch
from src.textures.texture_data import TextureData


class TextureButtonNinePatchConfig:
    boundaries = {
        "left": 16,
        "right": 16,
        "bottom": 6,
        "top": 9,
    }

    gold = {
        "nine_patch": PixelatedNinePatch,
        "main_tex": {
            **boundaries,
            "texture": TextureData.buttons[7],
        },
        "pressed_tex": {
            **boundaries,
            "texture": TextureData.buttons[9],
        },
        "hovered_tex": {
            **boundaries,
            "texture": TextureData.buttons[11],
        },
    }
