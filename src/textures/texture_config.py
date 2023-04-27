from arcade.gui import UITextureButton

from src.textures.pixelated_nine_patch import PixelatedNinePatch
from src.textures.texture_data import SpriteSheetSpecs


class TextureButtonNinePatchConfig:
    boundaries = {
        "left": 32,
        "right": 32,
        "bottom": 16,
        "top": 16,
    }

    gold = lambda: {
        "texture": {
            **TextureButtonNinePatchConfig.boundaries,
            "texture": lambda: SpriteSheetSpecs.buttons.load_one(7),
        },
        "texture_hovered": {
            **TextureButtonNinePatchConfig.boundaries,
            "texture": lambda: SpriteSheetSpecs.buttons.load_one(11),
        },
        "texture_pressed": {
            **TextureButtonNinePatchConfig.boundaries,
            "texture": lambda: SpriteSheetSpecs.buttons.load_one(9),
        },
    }


def load_nine_patch(config: dict) -> PixelatedNinePatch:
    tex_loader = config.pop("texture", None)

    if not callable(tex_loader):
        raise TypeError("should not be loaded yet!")

    kwargs = {
        "texture": tex_loader(),  # <---- at this point we access the TextureData
        **config,
    }
    return PixelatedNinePatch(**kwargs)


def load_ui_texture_button(texture_config: dict, text: str) -> UITextureButton:
    expected_keys = {"texture", "texture_hovered", "texture_pressed"}
    kwargs = {k: load_nine_patch(v) for k, v in texture_config.items()}

    if expected_keys - {*kwargs.keys()} != set():
        raise KeyError(
            f"Missing Key in {texture_config.keys()}: Expected {expected_keys=} got {kwargs.keys()=}"
        )

    return UITextureButton(**kwargs, text=text)
