from dataclasses import dataclass

import arcade
import pyglet
from arcade.hitbox import BoundingHitBoxAlgorithm

from src.utils.sprites.spritesheet import load_spritesheet

pyglet.font.add_file("./assets/alagard.ttf")


def _cross_platform_name(name: str) -> str:
    if pyglet.compat_platform == "linux":
        return name.lower()

    return name


class WindowData:
    width = 800
    height = 600
    scale = (width / 800, height / 600)
    title_background = arcade.load_texture("./assets/background_glacial_mountains.png")
    mission_background = arcade.load_texture("./assets/mb.png")

    tiles = load_spritesheet(
        "./assets/sprites/Isometric_MedievalFantasy_Tiles.png",
        sprite_height=17,
        sprite_width=16,
        columns=11,
        count=111,
        top_left_offset=(0, 0),
        hit_box_algorithm=BoundingHitBoxAlgorithm(),
    )

    fighters = arcade.load_spritesheet(
        "./assets/sprites/IsometricTRPGAssetPack_OutlinedEntities.png",
        sprite_width=16,
        sprite_height=16,
        columns=4,
        count=130,
        margin=1,
    )

    buttons = arcade.load_spritesheet(
        "./assets/sprites/buttons.png",
        sprite_height=16,
        sprite_width=48,
        columns=6,
        count=24,
        margin=0,
    )

    indicators = arcade.load_spritesheet(
        "./assets/sprites/TRPGIsometricAssetPack_MapIndicators.png",
        sprite_height=8,
        sprite_width=16,
        columns=2,
        count=6,
        margin=0,
    )

    window_icon = pyglet.image.load("./assets/icon.png")
    font = _cross_platform_name("Alagard")
