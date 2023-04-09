from __future__ import annotations

import math
from typing import NamedTuple

import arcade
import arcade.color
import arcade.key
from arcade import Window
from arcade.gui import UIAnchorLayout, UIImage, UIManager, UITextureButton
from arcade.gui.widgets.text import UILabel

from src.config import font_sizes
from src.engine.init_engine import eng
from src.gui import motion
from src.gui.buttons import nav_button, update_button
from src.gui.view_components import CommandBarSection, InfoPaneSection
from src.gui.views.missions import MissionsView
from src.gui.views.roster import RosterView
from src.gui.window_data import WindowData
from src.textures.pixelated_nine_patch import PixelatedNinePatch
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

        self.angle = 0

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

        self.start_banner_sprite.center_y = motion.harmonic_motion(
            10, 2, self.angle, v_shift=WindowData.height * 0.1
        ).y

    def animate_title_banner(self):
        if self.banner_sprite.alpha < 255:
            self.banner_sprite.alpha += 1

        if self.banner_sprite.scale < 2:
            self.banner_sprite.scale += 0.01

        self.banner_sprite.center_y = motion.harmonic_motion(
            10, 2, self.angle, v_shift=WindowData.height * 0.85
        ).y
        self.banner_sprite.center_x = motion.harmonic_motion(
            10, 1.5, self.angle * 2, phase_shift=WindowData.width / 2
        ).x

    def update_angle(self, delta_time):
        self.angle += delta_time / 2

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
        self.sprite_list.draw(pixelated=True)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G | arcade.key.ENTER:
                guild_view = GuildView()
                self.window.show_view(guild_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height

        self.start_banner_sprite.center_x = width / 2


class GuildViewButtons(NamedTuple):
    missions: UITextureButton
    roster: UITextureButton
    refresh_buttons: UITextureButton


class GuildView(arcade.View):
    """Draw a view displaying information about a guild"""

    def __init__(self):
        super().__init__()
        # InfoPane config.
        self.guild_label = UILabel(
            text=eng.game_state.guild.name,
            width=WindowData.width,
            font_size=font_sizes.TITLE,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=248,
            prevent_dispatch_view={False},
            margin=5,
            texts=[self.guild_label],
        )
        # CommandBar config
        self.buttons = GuildViewButtons(
            nav_button(lambda: MissionsView(self), "Missions"),
            nav_button(lambda: RosterView(self), "Roster"),
            update_button(on_click=eng.refresh_mission_board, text="New Missions"),
        )
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        # Add sections to section manager.
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.clear()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                title_view = TitleView()
                title_view.title_y = WindowData.height * 0.75
                title_view.initial_subtitle_y_pos = WindowData.height * 0.3
                self.window.show_view(title_view)

            case arcade.key.N:
                if eng.game_state.mission_board is not None:
                    eng.game_state.mission_board.clear_board()
                    eng.game_state.mission_board.fill_board(
                        max_enemies_per_room=3, room_amount=3
                    )

            case arcade.key.M:
                missions_view = MissionsView(parent=GuildView)
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView(parent=GuildView)
                self.window.show_view(roster_view)

            case arcade.key.ESCAPE:
                arcade.exit()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
