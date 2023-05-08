from __future__ import annotations

import json
from typing import Callable, NamedTuple

import arcade
import arcade.color
import arcade.key
import yaml
from arcade.gui import UITextureButton
from arcade.gui.widgets.text import UILabel
from src import config

from src.config import font_sizes
from src.engine.game_state import GameState
from src.engine.guild import Guild
from src.engine.init_engine import eng
from src.engine.persistence.dumpers import GameStateDumpers
from src.engine.persistence.game_state_repository import Format, GameStateRepository
from src.entities.entity import Entity
from src.gui.components.buttons import nav_button, update_button
from src.gui.generic_sections.command_bar import CommandBarSection
from src.gui.generic_sections.info_pane import InfoPaneSection
from src.gui.guild.missions import MissionsView
from src.gui.guild.roster import RosterView
from src.gui.window_data import WindowData


class HomeViewButtons(NamedTuple):
    missions: UITextureButton
    roster: UITextureButton
    refresh_buttons: UITextureButton


class HomeView(arcade.View):
    """Draw a view displaying information about a guild"""

    def __init__(self, parent_factory: Callable[[], arcade.View]):
        super().__init__()
        self.parent_factory = parent_factory
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
        self.buttons = HomeViewButtons(
            nav_button(
                lambda: MissionsView(
                    lambda: HomeView(parent_factory=self.parent_factory)
                ),
                "Missions",
            ),
            nav_button(
                lambda: RosterView(
                    lambda: HomeView(parent_factory=self.parent_factory)
                ),
                "Roster",
            ),
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
            case arcade.key.S:
                slot = 0
                if config.DEBUG:
                    formats = (Format.PICKLE, Format.YAML)
                    GameStateRepository.save(slot, fmts=formats)
                
                else:
                    GameStateRepository.save(slot)

            case arcade.key.L:
                # try:
                guild = GameStateRepository.load(0)
                eng.game_state.set_guild(guild)
                eng.game_state.set_team()

            # except Exception as error:
            # print(f"Loading Failed: {error}")

            case arcade.key.G:
                self.window.show_view(self.parent_factory())

            case arcade.key.N:
                if eng.game_state.mission_board is not None:
                    eng.game_state.mission_board.clear_board()
                    eng.game_state.mission_board.fill_board(
                        max_enemies_per_room=3, room_amount=3
                    )

            case arcade.key.M:
                missions_view = MissionsView(
                    parent_factory=lambda: HomeView(parent_factory=self.parent_factory)
                )
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView(
                    parent_factory=lambda: HomeView(parent_factory=self.parent_factory)
                )
                self.window.show_view(roster_view)

            case arcade.key.ESCAPE:
                arcade.exit()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
