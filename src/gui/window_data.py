import arcade
import pyglet
from dataclasses import dataclass
from pyglet.libs.win32.constants import WINDOWS_7_OR_GREATER

pyglet.font.add_file("./assets/alagard.ttf")

def _cross_platform_name(name: str) -> str:
    if pyglet.compat_platform not in (WINDOWS_7_OR_GREATER, "darwin"):
        return name.lower()

    return name

@dataclass
class WindowData:
    width = 800
    height = 600
    title_background = arcade.load_texture("./assets/background_glacial_mountains.png")
    mission_background = arcade.load_texture("./assets/mb.png")
    font = _cross_platform_name("Alagard")