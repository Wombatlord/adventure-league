from __future__ import annotations

import arcade
import arcade.color
import arcade.key
from arcade import Window

from src.gui.animation import harmonic
from src.gui.components.buttons import get_nav_handler
from src.gui.components.menu import LeafMenuNode, Menu, SubMenuNode
from src.gui.guild.home import HomeView
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
        navigate_to_guild = get_nav_handler(HomeView(parent_factory=TitleView))
        self.menu_options = [
            LeafMenuNode("Start", navigate_to_guild),
            SubMenuNode(
                "first",
                sub_menu=[
                    LeafMenuNode("x", lambda: print("a")),
                    LeafMenuNode("y", lambda: print("b")),
                    LeafMenuNode("z", lambda: print("c")),
                ],
            ),
            SubMenuNode(
                "second",
                sub_menu=[
                    LeafMenuNode("a", lambda: None),
                    LeafMenuNode("1", lambda: print("1")),
                    LeafMenuNode("2", lambda: print("2")),
                    SubMenuNode(
                        "3",
                        sub_menu=[
                            LeafMenuNode("4", lambda: print("4")),
                        ],
                    ),
                ],
            ),
            LeafMenuNode("Quit", arcade.exit, closes_menu=True),
        ]
        self.menu = Menu(
            menu_config=self.menu_options,
            pos=((WindowData.width / 2), (WindowData.height * 0.5)),
            area=(450, 50 * len(self.menu_options)),
        )
        self.menu.enable()

    def on_update(self, delta_time: float):
        self.update_angle(delta_time)
        self.animate_title_banner()
        self.animate_start_banner()

    def on_show_view(self):
        self.menu.enable()

    def on_hide_view(self):
        self.menu.disable()
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
        self.clear()
        arcade.draw_lrwh_rectangle_textured(
            0,
            0,
            WindowData.width,
            WindowData.height,
            SingleTextureSpecs.title_background.loaded,
        )
        self.menu.draw()
        self.sprite_list.draw(pixelated=True)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G | arcade.key.ENTER:
                g = HomeView(parent_factory=TitleView)
                self.window.show_view(g)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.menu.maintain_menu_positioning(width=width, height=height)
        self.menu.position_labels()
        self.start_banner_sprite.center_x = width / 2
        WindowData.width = width
        WindowData.height = height
