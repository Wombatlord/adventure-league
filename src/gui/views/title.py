from __future__ import annotations

import math
from typing import NamedTuple

import arcade
import arcade.color
import arcade.key
from arcade import Window

from src.gui.animation import harmonic
from src.gui.components.menu import ButtonRegistry, Menu
from src.gui.views.guild import GuildView
from src.gui.window_data import WindowData
from src.textures.texture_data import SingleTextureSpecs


class TitleView(arcade.View):
    def __init__(self, window: Window | None = None):
        super().__init__(window)
        self.initial_title_y_pos = -250
        self.initial_subtitle_y_pos = -50
        self.sprite_list = arcade.SpriteList()
        self.banner_sprite = arcade.Sprite(
            path_or_texture=SingleTextureSpecs.title_banner.loaded,
            center_x=WindowData.width / 2,
            center_y=self.initial_title_y_pos,
            scale=0,
        )
        self.banner_sprite.alpha = 0
        self.start_banner_sprite = arcade.Sprite(
            path_or_texture=SingleTextureSpecs.start_banner.loaded,
            center_x=WindowData.width / 2,
            center_y=WindowData.height * 0.1,
            scale=0,
        )
        self.start_banner_sprite.alpha = 0
        sprites = [self.banner_sprite, self.start_banner_sprite]
        for sprite in sprites:
            self.sprite_list.append(sprite)

        self.time = 0
        self.menu_options = [
            (
                "Start",
                lambda: GuildView(parent_factory=TitleView),
                ButtonRegistry.navigate,
            ),
            (
                "first",
                [
                    ("x", lambda: print("a"), ButtonRegistry.update),
                    ("y", lambda: print("b"), ButtonRegistry.update),
                    ("z", lambda: print("c"), ButtonRegistry.update),
                ],
                ButtonRegistry.update,
            ),
            (
                "second",
                [
                    ("a", lambda: None, ButtonRegistry.update),
                    ("1", lambda: print("1"), ButtonRegistry.update),
                    ("2", lambda: print("2"), ButtonRegistry.update),
                    (
                        "3",
                        [
                            ("4", lambda: print("4"), ButtonRegistry.update),
                        ],
                        ButtonRegistry.update,
                    ),
                ],
                ButtonRegistry.update,
            ),
            ("Quit", arcade.exit, ButtonRegistry.update),
        ]
        self.menu = Menu(
            menu_config=self.menu_options,
            pos=((WindowData.width / 2) - 225, (WindowData.height * 0.45)),
            area=(450, 350),
        )
        self.menu.build_menu(self.menu_options)
        self.menu.manager.enable()

    def on_update(self, delta_time: float):
        self.update_angle(delta_time)
        self.animate_title_banner()
        self.animate_start_banner()

    def on_hide_view(self):
        self.clear()

    def animate_start_banner(self):
        if self.banner_sprite.alpha == 255 and self.start_banner_sprite.alpha < 255:
            self.start_banner_sprite.alpha += 1

            if self.start_banner_sprite.scale < 2:
                self.start_banner_sprite.scale += 0.01

        self.start_banner_sprite.center_y = harmonic.harmonic_motion(
            10, 2, self.time, v_shift=WindowData.height * 0.1
        ).y

    def animate_title_banner(self):
        if self.banner_sprite.alpha < 255:
            self.banner_sprite.alpha += 1

        if self.banner_sprite.scale < 2:
            self.banner_sprite.scale += 0.01

        self.banner_sprite.center_y = harmonic.harmonic_motion(
            amplitude=10, period=2, theta=self.time, v_shift=WindowData.height * 0.85
        ).y
        self.banner_sprite.center_x = harmonic.harmonic_motion(
            amplitude=10,
            period=1.5,
            theta=self.time * 2,
            phase_shift=WindowData.width / 2,
        ).x

    def update_angle(self, delta_time):
        self.time += delta_time / 2

    def on_draw(self):
        """Draw the title screen"""
        # Draw the background image
        arcade.draw_lrwh_rectangle_textured(
            0,
            0,
            WindowData.width,
            WindowData.height,
            SingleTextureSpecs.title_background.loaded,
        )
        self.menu.manager.draw()
        self.sprite_list.draw(pixelated=True)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G | arcade.key.ENTER:
                self.window.show_view(GuildView(parent_factory=TitleView))

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
        self.menu.main_box.center = (width / 2, height * 0.45)
        self.start_banner_sprite.center_x = width / 2
