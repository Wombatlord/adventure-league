from __future__ import annotations

from typing import Callable

import arcade
import arcade.color
import arcade.key
from arcade.gui import UIWidget
from arcade.gui.widgets.text import UILabel

from src.config import font_sizes
from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.gui.buttons import get_nav_handler, nav_button, recruit_button, roster_button
from src.gui.gui_components import (
    box_containing_horizontal_label_pair,
    label_with_observer,
)
from src.gui.observer import observe
from src.gui.roster_view_sections import (
    RecruitmentPaneSection,
    RosterAndTeamPaneSection,
)
from src.gui.states import ViewStates
from src.gui.view_components import CommandBarSection, InfoPaneSection
from src.gui.window_data import WindowData


def entity_observer_widget(get_entity: Callable[[], Entity | None]):
    def entity_info_label(ui_label, merc: Entity | None) -> None:
        if merc is None:
            ui_label.text = "No stats to display."
            return

        ui_label.text = (
            f"{merc.name.name_and_title} "
            f"| LVL: {merc.fighter.level} "
            f"|  HP: {merc.fighter.hp} "
            f"| ATK: {merc.fighter.power} "
            f"| DEF: {merc.fighter.defence} "
        )

    recruit_info_observer = observe(
        get_observed_state=get_entity,
        sync_widget=entity_info_label,
    )

    entity_info = label_with_observer(
        label=f"",
        width=WindowData.width,
        height=50,
        align="center",
        font_size=font_sizes.BODY,
        color=arcade.color.WHITE,
        attach=recruit_info_observer,
        multiline=True,
    )
    entity_info_label(entity_info, get_entity())

    return entity_info


class RecruitmentView(arcade.View):
    def __init__(self, parent=None):
        super().__init__()
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE
        self.parent = parent

        # RecruitmentPane Config
        self.recruitment_pane_section = RecruitmentPaneSection(
            name="recruitment_pane_section",
            left=2,
            bottom=242,
            width=WindowData.width,
            height=WindowData.height,
            prevent_dispatch_view={False},
        )
        self.add_section(self.recruitment_pane_section)

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Press Enter to Recruit!",
            width=WindowData.width,
            height=50,
            multiline=True,
            font_size=font_sizes.SUBTITLE,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=arcade.color.WHITE,
        )

        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[
                self.instruction,
                entity_observer_widget(self.get_selected_entity),
                self._guild_funds_info_observer_widget(),
            ],
        )
        self.add_section(self.info_pane_section)

        # CommandBar Config
        self.recruitment_pane_buttons = [
            nav_button(lambda: RosterView(self.parent), "Roster"),
            nav_button(self.parent, "Guild"),
        ]

        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.recruitment_pane_buttons,
            prevent_dispatch_view={False},
        )
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.recruitment_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        self.info_pane_section.manager.on_update(0)

    def on_hide_view(self) -> None:
        self.recruitment_pane_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.command_bar_section.manager.disable()

    def get_selected_entity(self) -> Entity | None:
        return self.recruitment_pane_section.selected_entity

    def _guild_funds_info_observer_widget(self) -> UIWidget:
        def set_funds_label_text(ui_label: UILabel, funds: int) -> None:
            ui_label.text = f"{funds} gp"

        funds_text_observer = observe(
            get_observed_state=lambda: eng.game_state.guild.funds,
            sync_widget=set_funds_label_text,
        )

        guild_funds = box_containing_horizontal_label_pair(
            (
                ("Guild Coffers: ", "right", font_sizes.TITLE, arcade.color.WHITE),
                (
                    f"{eng.game_state.guild.funds}",
                    "left",
                    font_sizes.TITLE,
                    arcade.color.GOLD,
                    funds_text_observer,
                ),
            ),
            padding=(0, 0, 0, 150),
            size_hint=(1, None),
        )

        return guild_funds

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                self.window.show_view(self.parent)

            case arcade.key.R:
                self.window.show_view(RosterView(parent=self.parent))

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    state = ViewStates.ROSTER

    def __init__(self, parent):
        super().__init__()
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE
        self.parent = parent
        # RosterAndTeamPane Config
        self.roster_and_team_pane_section = RosterAndTeamPaneSection(
            left=2,
            bottom=242,
            width=WindowData.width,
            height=WindowData.height,
            prevent_dispatch_view={False},
        )

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Assign members to the team before embarking on a mission!",
            width=WindowData.width,
            height=75,
            multiline=True,
            font_size=font_sizes.SUBTITLE,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=arcade.color.WHITE,
        )

        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, entity_observer_widget(self.get_selected_entity)],
        )

        self.roster_pane_buttons = [
            nav_button(lambda: RecruitmentView(self.parent), "Recruit"),
            nav_button(self.parent, "Guild"),
        ]

        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.roster_pane_buttons,
            prevent_dispatch_view={False},
        )

        self.add_section(self.roster_and_team_pane_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def get_selected_entity(self) -> Entity | None:
        return self.roster_and_team_pane_section.selected_entity

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.roster_and_team_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

    def on_hide_view(self) -> None:
        self.roster_and_team_pane_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.command_bar_section.manager.disable()

    def on_draw(self) -> None:
        self.clear()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                self.window.show_view(self.parent)

            case arcade.key.R:
                self.window.show_view(RecruitmentView(parent=self.parent))

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height
