from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from src.gui.guild.equipment import EquipView

if TYPE_CHECKING:
    from src.gui.guild.home import HomeView

import arcade
import arcade.color
import arcade.key
from arcade.gui import UIWidget
from arcade.gui.widgets.text import UILabel

from src.config import font_sizes
from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.gui.components.buttons import nav_button
from src.gui.components.layouts import (box_containing_horizontal_label_pair,
                                        get_colored_label)
from src.gui.components.observer import observe
from src.gui.generic_sections.command_bar import CommandBarSection
from src.gui.generic_sections.info_pane import InfoPaneSection
from src.gui.guild.roster_sections import (RecruitmentPaneSection,
                                           RosterAndTeamPaneSection)
from src.gui.window_data import WindowData


def entity_observer_widget(get_entity: Callable[[], Entity | None]) -> UILabel:
    def entity_info_label(ui_label, merc: Entity | None) -> None:
        if merc is None:
            ui_label.text = "No stats to display."
            return

        ui_label.text = (
            f"{merc.name.name_and_title} "
            f"| LVL: {merc.fighter.leveller.current_level} "
            f"|  HP: {merc.fighter.health.current} "
            f"| ATK: {int(merc.fighter.modifiable_stats.current.power)} "
            f"| DEF: {int(merc.fighter.modifiable_stats.current.defence)} "
        )

    recruit_info_observer = observe(
        get_observed_state=get_entity,
        sync_widget=entity_info_label,
    )

    entity_info = get_colored_label(
        label=f"",
        width=WindowData.width,
        height=50,
        align="center",
        font_size=font_sizes.SUBTITLE,
        color=arcade.color.WHITE,
        attach=recruit_info_observer,
        multiline=True,
    )
    entity_info_label(entity_info, get_entity())
    return entity_info


class RecruitmentView(arcade.View):
    def __init__(self, parent_factory):
        super().__init__()
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE
        self.parent_factory = parent_factory

        # RecruitmentPane Config
        self.recruitment_pane_section = RecruitmentPaneSection(
            name="recruitment_pane_section",
            left=2,
            bottom=342,
            width=self.window.width,
            height=self.window.height,
            prevent_dispatch_view={False},
        )
        self.add_section(self.recruitment_pane_section)

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Press Enter to Recruit!",
            width=WindowData.width,
            height=65,
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
            height=288,
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
            nav_button(lambda: RosterView(self.parent_factory), "Roster"),
            nav_button(self.parent_factory, "Guild"),
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

    def on_hide_view(self) -> None:
        self.recruitment_pane_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.command_bar_section.manager.disable()
        self.clear()

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
                ("Guild Coffers: ", "right", font_sizes.SUBTITLE, arcade.color.WHITE),
                (
                    f"{eng.game_state.guild.funds} gp",
                    "left",
                    font_sizes.SUBTITLE,
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
                g = self.parent_factory()
                self.window.show_view(g)

            case arcade.key.R:
                self.window.show_view(RosterView(parent_factory=self.parent_factory))

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    def __init__(self, parent_factory):
        super().__init__()
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE
        self.parent_factory: Callable[[], HomeView] = parent_factory
        # RosterAndTeamPane Config
        self.roster_and_team_pane_section = RosterAndTeamPaneSection(
            left=2,
            bottom=342,
            width=self.window.width,
            height=self.window.height,
            prevent_dispatch_view={False},
        )

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Assign members to the team before embarking on a mission!",
            width=WindowData.width,
            height=85,
            multiline=True,
            font_size=font_sizes.SUBTITLE,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=arcade.color.WHITE,
        )
        self.add_section(self.roster_and_team_pane_section)

        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=288,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, entity_observer_widget(self.get_selected_entity)],
        )
        self.add_section(self.info_pane_section)

        self.roster_pane_buttons = [
            nav_button(lambda: RecruitmentView(self.parent_factory), "Recruit"),
            nav_button(self.parent_factory, "Guild"),
        ]

        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.roster_pane_buttons,
            prevent_dispatch_view={False},
        )
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
        self.clear()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                g = self.parent_factory()
                self.window.show_view(g)

            case arcade.key.R:
                self.window.show_view(
                    RecruitmentView(parent_factory=self.parent_factory)
                )

            case arcade.key.X:
                equip_view = EquipView(
                    self.get_selected_entity().fighter,
                    parent_factory=lambda: RosterView(
                        parent_factory=self.parent_factory
                    ),
                )
                self.window.show_view(equip_view)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
