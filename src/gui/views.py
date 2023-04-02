from __future__ import annotations

import arcade
import arcade.color
import arcade.key
from arcade import Window
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel

from src.engine.init_engine import eng
from src.entities.actions import MoveAction
from src.entities.inventory import InventoryItem
from src.gui.buttons import (
    end_turn_button,
    get_end_turn_handler,
    get_new_missions_button,
    get_switch_to_recruitment_pane_handler,
    get_switch_to_roster_and_team_panes_handler,
    nav_button,
    recruit_button,
    roster_button,
)
from src.gui.combat_sections import CombatGridSection
from src.gui.gui_components import box_containing_horizontal_label_pair
from src.gui.gui_utils import Cycle
from src.gui.missions_view_section import MissionsSection
from src.gui.roster_view_sections import (
    RecruitmentPaneSection,
    RosterAndTeamPaneSection,
)
from src.gui.states import ViewStates
from src.gui.view_components import CommandBarSection, InfoPaneSection
from src.gui.window_data import WindowData
from src.textures.texture_data import SingleTextureSpecs
from src.utils.input_capture import BaseInputMode, Selection
from src.world.node import Node


class TitleView(arcade.View):
    def __init__(self, window: Window | None = None):
        super().__init__(window)
        self.background = SingleTextureSpecs.title_background.loaded
        self.title_y = -10
        self.start_y = -10

    def on_show_view(self):
        """Called when switching to this view"""
        pass

    def on_update(self, delta_time: float):
        if self.title_y < WindowData.height * 0.75:
            self.title_y += 5

        if (
            self.title_y == WindowData.height * 0.75
            and self.start_y < WindowData.height * 0.3
        ):
            self.start_y += 5

    def on_draw(self):
        """Draw the title screen"""
        self.clear()

        # Draw the background image
        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowData.width, WindowData.height, self.background
        )

        # Draw the scrolling title text. Scrolling is handled in self.on_update().
        arcade.draw_text(
            "ADVENTURE LEAGUE!",
            WindowData.width / 2,
            self.title_y,
            arcade.color.GOLD,
            font_name=WindowData.font,
            font_size=40,
            anchor_x="center",
        )

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


class GuildView(arcade.View):
    """Draw a view displaying information about a guild"""

    state = ViewStates.GUILD

    def __init__(self, window: Window = None):
        super().__init__(window)
        # InfoPane config.
        self.guild_label = UILabel(
            text=eng.game_state.guild.name,
            width=WindowData.width,
            font_size=18,
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
        self.buttons = [
            nav_button(MissionsView, "Missions"),
            nav_button(RosterView, "Roster"),
            get_new_missions_button(),
        ]
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

    def on_draw(self) -> None:
        self.clear()

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
                missions_view = MissionsView()
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView()
                self.window.show_view(roster_view)

            case arcade.key.ESCAPE:
                arcade.exit()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    state = ViewStates.ROSTER

    def __init__(self, window: Window = None):
        super().__init__(window)
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE

        # RosterAndTeamPane Config
        self.roster_and_team_pane_section = RosterAndTeamPaneSection(
            left=2,
            bottom=242,
            width=WindowData.width - 2,
            height=WindowData.height - 2,
            prevent_dispatch_view={False},
        )

        # RecruitmentPane Config
        self.recruitment_pane_section = RecruitmentPaneSection(
            name="recruitment_pane_section",
            left=2,
            bottom=242,
            width=WindowData.width - 2,
            height=WindowData.height - 2,
            prevent_dispatch_view={False},
        )

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Assign members to the team before embarking on a mission!",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
            text_color=self.color,
        )
        self.entity_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
        )

        self.guild_funds = box_containing_horizontal_label_pair(
            (
                (" ", "right", 18, arcade.color.WHITE),
                (" ", "left", 18, arcade.color.GOLD),
            ),
            padding=(0, 0, 0, 50),
            size_hint=(1, None),
        )

        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, self.entity_info, self.guild_funds],
        )

        # CommandBar Config
        self.recruitment_pane_buttons = [
            roster_button(self),
            nav_button(GuildView, "Guild"),
        ]
        self.roster_pane_buttons = [
            recruit_button(self),
            nav_button(GuildView, "Guild"),
        ]
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.roster_pane_buttons,
            prevent_dispatch_view={False},
        )

        self.show_roster = get_switch_to_roster_and_team_panes_handler(self)
        self.show_recruitment = get_switch_to_recruitment_pane_handler(self)

        self.add_section(self.roster_and_team_pane_section)
        self.add_section(self.recruitment_pane_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def _roster_entity(self) -> None:
        """Sets self.merc to the selected entry in the roster scroll window.
        Allows the InfoPaneSection to display entity reference from RosterAndTeamPaneSection
        """
        if (
            self.roster_and_team_pane_section.pane_selector.pos == 0
            and len(self.roster_and_team_pane_section.roster_scroll_window.items) > 0
        ):
            self.merc = self.roster_and_team_pane_section.roster_scroll_window.items[
                self.roster_and_team_pane_section.roster_scroll_window.position.pos
            ]

    def _team_entity(self) -> None:
        """Sets self.merc to the selected entry in the team scroll window.
        Allows the InfoPaneSection to display entity reference from RosterAndTeamPaneSection
        """
        if (
            self.roster_and_team_pane_section.pane_selector.pos == 1
            and len(self.roster_and_team_pane_section.team_scroll_window.items) > 0
        ):
            self.merc = self.roster_and_team_pane_section.team_scroll_window.items[
                self.roster_and_team_pane_section.team_scroll_window.position.pos
            ]

    def _recruits_entity(self) -> None:
        """Sets self.merc to the selected entry in the recruitment scroll window.
        Allows the InfoPaneSection to display entity reference from RecruitmentPaneSection
        """
        if len(self.recruitment_pane_section.recruitment_scroll_window.items) > 0:
            self.merc = self.recruitment_pane_section.recruitment_scroll_window.items[
                self.recruitment_pane_section.recruitment_scroll_window.position.pos
            ]

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.recruitment_pane_section.manager.enable()
        self.roster_and_team_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

        self.recruitment_pane_section.enabled = False

    def on_hide_view(self) -> None:
        self.recruitment_pane_section.manager.disable()
        self.roster_and_team_pane_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.command_bar_section.manager.disable()

    def on_update(self, delta_time: float):
        self.merc = None
        if self.state == ViewStates.ROSTER:
            self._roster_entity()
            self._team_entity()

        if self.state == ViewStates.RECRUIT:
            self._recruits_entity()

        if self.merc is None:
            self.entity_info.text = ""
        else:
            self.entity_info.text = f"{self.merc.name.name_and_title} | LVL: {self.merc.fighter.level}  |  HP: {self.merc.fighter.hp}  |  ATK: {self.merc.fighter.power}  |  DEF: {self.merc.fighter.defence}"

    def on_draw(self) -> None:
        self.clear()

    def _log_input(self, symbol, modifiers):
        ...

    def _log_state(self):
        ...

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self._log_input(symbol, modifiers)

        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.R:
                if self.state == ViewStates.ROSTER:
                    self.show_recruitment()

                elif self.state == ViewStates.RECRUIT:
                    self.show_roster()

        self._log_state()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class MissionsView(arcade.View):
    state = ViewStates.MISSIONS

    def __init__(self, window: Window = None):
        super().__init__(window)
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
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
        )
        self.team_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
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
        self.buttons: list[UIFlatButton] = [nav_button(GuildView, "Guild")]
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

    def on_draw(self) -> None:
        self.clear()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.DOWN:
                self.selection.decr()

            case arcade.key.UP:
                self.selection.incr()

            case arcade.key.RETURN:
                eng.selected_mission = self.mission_section.mission_selection.pos
                eng.init_dungeon()
                if not eng.game_state.dungeon.cleared:
                    if len(eng.game_state.guild.team.members) > 0:
                        self.window.show_view(BattleView())


class ActionSelectionInputMode(BaseInputMode):
    name: str

    def __init__(self, view: BattleView, selection: Selection, name: str):
        super().__init__(self)
        self.selection = selection
        self.name = name
        self.view = view

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.TAB:
                self.view.next_input_mode()
            case arcade.key.UP:
                self.selection.prev()
            case arcade.key.DOWN:
                self.selection.next()
            case arcade.key.SPACE:
                self.selection.confirm()


class NoInputMode(BaseInputMode):
    pass


class BattleView(arcade.View):
    input_mode: BaseInputMode
    selections: dict[str, Selection]

    def __init__(self, window: Window = None):
        super().__init__(window)

        self.combat_grid_section = CombatGridSection(
            left=0,
            bottom=WindowData.height / 2,
            width=WindowData.width,
            height=WindowData.height / 2,
            prevent_dispatch_view={False},
        )

        # CommandBar config
        self.buttons = [
            end_turn_button(
                lambda _: self.input_mode.on_key_press(arcade.key.SPACE, 0)
            ),
        ]

        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        self.selections = {}
        self.item_menu_mode_allowed = True
        self.input_modes = {}
        self.input_mode = NoInputMode(self)
        self._default_input_mode = None
        self.confirm_selection = lambda: None
        self.bind_input_modes()
        self.add_section(self.command_bar_section)
        self.add_section(self.combat_grid_section)
        eng.init_combat()

    def bind_input_modes(self):
        if not self.selections:
            self.input_mode = NoInputMode(self)
            return

        self.input_modes = {}
        prev_name = None
        for name, selection in sorted(
            self.selections.items(), key=lambda s: int(s[0] != MoveAction.name)
        ):
            self.input_modes[name] = ActionSelectionInputMode(self, selection, name)
            if prev_name:
                self.input_modes[name].set_next_mode(self.input_modes[prev_name])
            prev_name = name

        self._default_input_mode = self.input_modes[MoveAction.name]
        self.reset_input_mode()

    def next_input_mode(self):
        self.input_mode = self.input_mode.get_next_mode()

    def reset_input_mode(self):
        self.input_mode = self._default_input_mode

    def on_show_view(self):
        self.command_bar_section.manager.enable()
        eng.combat_dispatcher.volatile_subscribe(
            topic="await_input",
            handler_id="BattleView.set_input_request",
            handler=self.set_action_selection,
        )

    def on_draw(self):
        self.clear()

    def set_action_selection(self, event):
        if requester := event.get("await_input"):
            if requester.owner.ai:
                return

        eng.await_input()

        choices = event.get("choices")
        selections = {}
        no_op = lambda: None

        for name, options in choices.items():
            if not options:
                continue

            hide_stuff = no_op
            if name == MoveAction.name:
                hide_stuff = lambda: self.combat_grid_section.hide_path()

            def _on_confirm(option_index: int) -> bool:
                hide_stuff()
                self.reset_input_mode()
                eng.input_received()
                return options[option_index]["on_confirm"](option_index)

            selections[name] = Selection(
                options=[opt["subject"] for opt in options],
                default=0,
            ).set_confirmation(_on_confirm)

            update_selection = no_op
            if name == MoveAction.name:
                update_selection = lambda: self.combat_grid_section.show_path(
                    selections[name].current
                )

            selections[name].set_on_change_selection(update_selection)

        self.selections = selections
        self.bind_input_modes()

    def on_key_release(self, _symbol: int, _modifiers: int):
        if not self.combat_grid_section.cam_controls.on_key_release(_symbol):
            return

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        print(f"{self.__class__}.on_key_press called with '{chr(symbol)}'")
        if not self.combat_grid_section.cam_controls.on_key_press(symbol):
            return

        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    guild_view = GuildView()
                    self.window.show_view(guild_view)

        self.input_mode.on_key_press(symbol, modifiers)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height
