from __future__ import annotations

import arcade
import arcade.color
import arcade.key
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel

from src.engine.init_engine import eng
from src.gui.components.buttons import nav_button
from src.gui.components.scroll_window import Cycle
from src.gui.sections.command_bar import CommandBarSection
from src.gui.sections.info_pane import InfoPaneSection
from src.gui.sections.missions_section import MissionsSection
from src.gui.views.combat import CombatView
from src.gui.window_data import WindowData


class MissionsView(arcade.View):
    def __init__(self, parent_factory: arcade.View):
        super().__init__()
        self.parent_factory = parent_factory
        self.margin = 5
        self.selection = Cycle(
            3, 2
        )  # 3 missions on screen, default selected (2) is the top visually.

        self.mission_section = MissionsSection(
            left=0,
            bottom=242,
            width=WindowData.width,
            height=WindowData.height - 242,
            prevent_dispatch_view={False},
            missions=eng.game_state.mission_board.missions,
        )

        # InfoPane config
        self.instruction = UILabel(
            text="",
            width=WindowData.width,
            height=50,
            font_size=24,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
        )
        self.team_info = UILabel(
            text="",
            width=WindowData.width,
            height=75,
            font_size=24,
            font_name=WindowData.font,
            multiline=True,
            align="center",
            size_hint=(1, None),
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, self.team_info],
        )

        # CommandBar Config
        self.buttons: list[UIFlatButton] = [nav_button(self.parent_factory, "Guild")]
        self.command_bar_section: CommandBarSection = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        self.add_section(self.mission_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.mission_section.manager.enable()
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        # Prepare text for display in InfoPaneSection.
        if len(eng.game_state.team.members) > 0:
            self.instruction.text = "Press Enter to Embark on a Mission!"
            self.team_info.text = (
                f"{len(eng.game_state.team.members)} Guild Members are ready to Embark!"
            )
            self.instruction.label.color = arcade.color.GOLD
            self.team_info.label.color = arcade.color.GOLD

        else:
            self.instruction.text = "No Guild Members are assigned to a team!"
            self.instruction.label.color = arcade.color.RED_DEVIL
            self.team_info.text = (
                "Assign Guild Members to a Team from the Roster before Embarking!"
            )
            self.team_info.label.color = arcade.color.RED_DEVIL

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.mission_section.manager.disable()
        self.clear()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                g = self.parent_factory
                self.window.show_view(g())

            case arcade.key.DOWN:
                self.selection.decr()

            case arcade.key.UP:
                self.selection.incr()

            case arcade.key.RETURN:
                eng.selected_mission = self.mission_section.mission_selection.pos
                eng.init_dungeon()
                if not eng.game_state.dungeon.cleared:
                    if len(eng.game_state.guild.team.members) > 0:
                        self.window.show_view(
                            CombatView(parent_factory=self.parent_factory)
                        )
