from dataclasses import dataclass

import arcade
import pyglet

pyglet.font.add_file("./assets/alagard.ttf")


def _cross_platform_name(name: str) -> str:
    if pyglet.compat_platform == "linux":
        return name.lower()

    return name


@dataclass
class WindowData:
    width = 800
    height = 600
    title_background = arcade.load_texture("./assets/background_glacial_mountains.png")
    mission_background = arcade.load_texture("./assets/mb.png")
    window_icon = pyglet.image.load("./assets/icon.png")
    font = _cross_platform_name("Alagard")
