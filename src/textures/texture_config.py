from arcade.gui import UITextureButton

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
        "main_texture": {
            **boundaries,
            "texture": lambda: TextureData.buttons[
                7
            ],  # <-- this says how to access texture data
        },
        "hovered_texture": {
            **boundaries,
            "texture": lambda: TextureData.buttons[11],
        },
        "pressed_texture": {
            **boundaries,
            "texture": lambda: TextureData.buttons[9],
        },
    }


def load_nine_patch(config: dict) -> PixelatedNinePatch:
    tex_loader = {**config}.pop("texture")

    if not callable(tex_loader):
        raise TypeError("should not be loaded yet!")

    kwargs = {
        **config,
        "texture": tex_loader(),  # <---- at this point we access the TextureData
    }
    return PixelatedNinePatch(**kwargs)


def load_ui_texture_button(texture_config: dict, text: str) -> UITextureButton:
    expected_keys = ("main_texture", "hovered_texture", "pressed_texture")
    kwargs = {k: load_nine_patch(v) for k, v in texture_config.items()}

    for key in expected_keys:
        if key not in kwargs.keys():
            raise KeyError(
                f"Missing Key in {texture_config.keys()}: Expected {expected_keys=} got {kwargs.keys()=}"
            )

    mt = kwargs["main_texture"]
    ht = kwargs["hovered_texture"]
    pt = kwargs["pressed_texture"]

    return UITextureButton(
        texture=mt, texture_hovered=ht, texture_pressed=pt, text=text
    )
