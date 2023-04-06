from __future__ import annotations

from typing import NamedTuple

import arcade
import arcade.color
import arcade.key
from arcade import Window
from arcade.gui import UITextureButton
from arcade.gui.widgets.text import UILabel

from src.config import font_sizes
from src.engine.init_engine import eng
from src.gui.buttons import nav_button, update_button
from src.gui.view_components import CommandBarSection, InfoPaneSection
from src.gui.views.missions import MissionsView
from src.gui.views.roster import RosterView
from src.gui.window_data import WindowData
from src.textures.texture_data import SingleTextureSpecs


class TitleView(arcade.View):
    def __init__(self, window: Window | None = None):
        super().__init__(window)
        self.background = SingleTextureSpecs.title_background.loaded
        self.banner = SingleTextureSpecs.banner.loaded
        self.title_y = -10
        self.start_y = -10
        self.sprite_list = arcade.SpriteList()
        self.banner_sprite = arcade.Sprite(
            self.banner, center_x=WindowData.width / 2, center_y=-250, scale=2
        )
        self.sprite_list.append(self.banner_sprite)

    def on_update(self, delta_time: float):
        if self.banner_sprite.center_y < WindowData.height * 0.85:
            self.banner_sprite.center_y += 5

        if self.banner_sprite.center_y > WindowData.height * 0.85:
            self.banner_sprite.center_y = WindowData.height * 0.85
        if (
            self.banner_sprite.center_y == WindowData.height * 0.85
            and self.start_y < WindowData.height * 0.3
        ):
            self.start_y += 5

    def on_draw(self):
        """Draw the title screen"""

        # Draw the background image
        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowData.width, WindowData.height, self.background
        )

        self.sprite_list.draw(pixelated=True)

        arcade.draw_text(
            "Press G for a Guild View!",
            WindowData.width / 2,
            self.start_y,
            arcade.color.GOLDENROD,
            font_name=WindowData.font,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height

        self.banner_sprite.center_x = WindowData.width // 2


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
            height=148,
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
        self.clear()

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                title_view = TitleView()
                title_view.title_y = WindowData.height * 0.75
                title_view.start_y = WindowData.height * 0.3
                self.window.show_view(title_view)

            case arcade.key.N:
                if eng.game_state.mission_board is not None:
                    eng.game_state.mission_board.clear_board()
                    eng.game_state.mission_board.fill_board(
                        max_enemies_per_room=3, room_amount=3
                    )

            case arcade.key.M:
                missions_view = MissionsView(parent=self)
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView(parent=self)
                self.window.show_view(roster_view)

            case arcade.key.ESCAPE:
                arcade.exit()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
