from typing import Callable

import arcade
import arcade.color
import arcade.key
from arcade import Window
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel

from src.engine.init_engine import eng
from src.gui.sections import CommandBarSection, InfoPaneSection, RecruitmentPaneSection
from src.gui.buttons import nav_button, get_new_missions_button
from src.gui.combat_screen import CombatScreen
from src.gui.gui_utils import Cycle, ScrollWindow
from src.gui.mission_card import MissionCard
from src.gui.roster_view_components import draw_panels
from src.gui.states import ViewStates
from src.gui.window_data import WindowData


class TitleView(arcade.View):
    def __init__(self, window: Window | None = None):
        super().__init__(window)
        self.background = WindowData.title_background
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
            size_hint=(1,None)
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=32,
            width=WindowData.width,
            height=148,
            prevent_dispatch_view = {False},
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
            height=30,
            buttons=self.buttons,
            prevent_dispatch_view = {False}
        )
        # Add sections to section manager.
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)
    
    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        self.info_pane_section.setup()
        self.command_bar_section.setup()
        
    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        # populate_guild_view_info_panel()

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

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    state = ViewStates.ROSTER

    def __init__(self, window: Window = None):
        super().__init__(window)
        self.margin = 5
        self.col_select = Cycle(2)
        self.row_height = 25
        self.roster_pane = 0
        self.team_pane = 1
        self.merc = None
        self.color = arcade.color.WHITE
        self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
        self.team_scroll_window = ScrollWindow(eng.game_state.guild.team.members, 10, 10)
        # self.recruitment_scroll_window = ScrollWindow(eng.game_state.entity_pool.pool, 10, 10)
        
        # RecruitmentPane Config
        self.recruitment_pane_section = RecruitmentPaneSection(
            left=2,
            bottom=182,
            width = WindowData.width - 2,
            height = WindowData.height - 2,
            prevent_dispatch_view = {False},
        )
        
        # InfoPane Config
        self.instruction = UILabel(
            text=f"Assign members to the team before embarking on a mission!",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1,1),
            text_color=self.color
        )
        self.entity_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1,1)
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=32,
            width=WindowData.width,
            height=148,
            prevent_dispatch_view = {False},
            margin=self.margin,
            texts=[self.instruction, self.entity_info],
        )
        
        # CommandBar Config
        self.recruitment_pane_buttons = [
            self.roster_button(),
            nav_button(GuildView, "Guild"),
        ]
        self.roster_pane_buttons = [
            self.recruit_button(),
            nav_button(GuildView, "Guild"),
        ]
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=30,
            buttons=self.roster_pane_buttons,
            prevent_dispatch_view = {False}
        )
        
        self.add_section(self.recruitment_pane_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def display_recruits(self, event: UIEvent) -> None:
        """Handler for recruit_button.
        Used to swap the roster and recruitment command bar.
        Instatiates a fresh ScrollWindow, updates the ViewState,
        then swap the command bar buttons and recomposes the UI.

        Args:
            event (UIEvent): The UIEvent which called this handler.
        """
        self.state = ViewStates.RECRUIT
        self.recruitment_pane_section.enabled = True
        self.command_bar_section.buttons = self.recruitment_pane_buttons
        self.command_bar_section.setup()

    def display_roster(self, event: UIEvent) -> None:
        """Handler for roster_button.
        Used to swap the roster and recruitment command bar.
        Instatiates a fresh ScrollWindow, updates the ViewState,
        then swaps the command bar buttons and recomposes the UI.

        Args:
            event (UIEvent): The UIEvent which called this handler.
        """
        self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
        self.state = ViewStates.ROSTER
        self.recruitment_pane_section.enabled = False
        self.command_bar_section.buttons = self.roster_pane_buttons
        self.command_bar_section.setup()

    def recruit_button(self) -> UIFlatButton:
        """Attached Handler will change from displaying the roster & team panes
        to showing recruits available for hire, with the appropriate command bar.

        Returns:
            UIFlatButton: Button with attached handler.
        """
        btn = UIFlatButton(
            text="Recruit "
        )  # Space at the end here to stop the t getting clipped when drawn.
        btn.on_click = self.display_recruits
        return btn

    def roster_button(self) -> UIFlatButton:
        """Attached Handler will change from displaying the roster & team panes
        to showing recruits available for hire, with the appropriate command bar.

        Returns:
            UIFlatButton: Button with attached handler.
        """
        btn = UIFlatButton(text="Roster")
        btn.on_click = self.display_roster
        return btn

    def _roster_entity(self) -> None:
        """Sets self.merc to the selected entry in the roster scroll window.
        """
        if self.col_select.pos == 0 and len(self.roster_scroll_window.items) > 0:
                self.merc = self.roster_scroll_window.items[
                    self.roster_scroll_window.position.pos
                ]
    
    def _team_entity(self) -> None:
        """Sets self.merc to the selected entry in the team scroll window.
        """
        if self.col_select.pos == 1 and len(self.team_scroll_window.items) > 0:
                self.merc = self.team_scroll_window.items[
                    self.team_scroll_window.position.pos
                ]
    
    def _recruits_entity(self) -> None:
        """Sets self.merc to the selected entry in the recruitment scroll window.
        """
        if len(self.recruitment_pane_section.recruitment_scroll_window.items) > 0:
                self.merc = self.recruitment_pane_section.recruitment_scroll_window.items[
                    self.recruitment_pane_section.recruitment_scroll_window.position.pos
                ]
    
    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.recruitment_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        
        self.info_pane_section.setup()
        self.recruitment_pane_section.setup()
        self.command_bar_section.setup()

        self.recruitment_pane_section.enabled = False
        
    def on_hide_view(self) -> None:
        self.recruitment_pane_section.manager.disable()
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
            self.entity_info.text = f"LVL: {self.merc.fighter.level}  |  HP: {self.merc.fighter.hp}  |  ATK: {self.merc.fighter.power}  |  DEF: {self.merc.fighter.defence}"
        
    def on_draw(self) -> None:
        self.clear()
        if self.state == ViewStates.ROSTER:
            draw_panels(
                margin=self.margin,
                col_select=self.col_select,
                height=WindowData.height,
                width=WindowData.width,
                row_height=self.row_height,
                roster_scroll_window=self.roster_scroll_window,
                team_scroll_window=self.team_scroll_window,
            )

        # if self.state == ViewStates.RECRUIT:
            # draw_recruiting_panel(
            #     margin=self.margin,
            #     height=WindowData.height,
            #     row_height=self.row_height,
            #     recruitment_scroll_window=self.recruitment_scroll_window,
            # )

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
                    self.state = ViewStates.RECRUIT
                    self.recruitment_pane_section.enabled = True
                    self.command_bar_section.buttons = self.recruitment_pane_buttons
                    self.command_bar_section.setup()

                elif self.state == ViewStates.RECRUIT:
                    # reinstantiate the roster_scroll_window to ensure new recruits are present.
                    self.recruitment_pane_section.enabled = False
                    self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
                    self.state = ViewStates.ROSTER
                    self.command_bar_section.buttons = self.roster_pane_buttons
                    self.command_bar_section.setup()

            case arcade.key.RIGHT:
                self.col_select.incr()

            case arcade.key.LEFT:
                self.col_select.decr()

            case arcade.key.UP:
                if self.state == ViewStates.ROSTER:
                    if self.col_select.pos == 0:
                        self.roster_scroll_window.decr_selection()

                    if self.col_select.pos == 1:
                        self.team_scroll_window.decr_selection()

                # elif self.state == ViewStates.RECRUIT:
                #     self.recruitment_scroll_window.decr_selection()
                #     self.recruitment_pane_section.pos = self.recruitment_scroll_window.position.pos

            case arcade.key.DOWN:
                if self.state == ViewStates.ROSTER:
                    if self.col_select.pos == 0:
                        self.roster_scroll_window.incr_selection()

                    if self.col_select.pos == 1:
                        self.team_scroll_window.incr_selection()

                # elif self.state == ViewStates.RECRUIT:
                #     self.recruitment_scroll_window.incr_selection()

            case arcade.key.ENTER:
                if self.state == ViewStates.ROSTER:
                    if (
                        self.col_select.pos == self.roster_pane
                        and len(self.roster_scroll_window.items) > 0
                    ):
                        # Move merc from ROSTER to TEAM. Increase Cycle.length for team, decrease Cycle.length for roster.
                        # Assign to Team & Remove from Roster.
                        self.team_scroll_window.append(
                            self.roster_scroll_window.selection
                        )
                        eng.game_state.guild.team.assign_to_team(
                            self.roster_scroll_window.selection
                        )
                        self.roster_scroll_window.pop()

                        # Update Engine state.
                        eng.game_state.guild.roster = self.roster_scroll_window.items
                        eng.game_state.guild.team.members = self.team_scroll_window.items

                    if (
                        self.col_select.pos == self.team_pane
                        and len(self.team_scroll_window.items) > 0
                    ):
                        # Move merc from TEAM to ROSTER
                        self.roster_scroll_window.append(
                            self.team_scroll_window.selection
                        )

                        # Remove from Team array
                        self.team_scroll_window.pop()

                        # Update Engine state.
                        eng.game_state.guild.roster = self.roster_scroll_window.items
                        eng.game_state.guild.team.members = self.team_scroll_window.items

                # elif self.state == ViewStates.RECRUIT:
                #     if len(eng.game_state.guild.roster) + len(eng.game_state.team.members) < eng.game_state.guild.roster_limit:
                #         eng.recruit_entity_to_guild(
                #             eng.game_state.entity_pool.pool.index(
                #                 self.recruitment_scroll_window.selection
                #             )
                #         )
                #         self.recruitment_scroll_window.pop()

        self._log_state()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.recruitment_pane_section.width = width - self.recruitment_pane_section.margin
        
        WindowData.width = width
        WindowData.height = height


class MissionsView(arcade.View):
    state = ViewStates.MISSIONS

    def __init__(self, window: Window = None):
        super().__init__(window)
        self.background = WindowData.mission_background
        self.margin = 5
        self.selection = Cycle(
            3, 2
        )  # 3 missions on screen, default selected (2) is the top visually.
        self.combat_screen = CombatScreen()
        
        # InfoPane config
        self.instruction = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1,1)
        )
        self.team_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1,1)
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=32,
            width=WindowData.width,
            height=148,
            prevent_dispatch_view = {False},
            margin=self.margin,
            texts=[self.instruction, self.team_info],
        )
        
        # CommandBar Config
        self.buttons: list[UIFlatButton] = [nav_button(GuildView, "Guild")]
        self.command_bar_section: CommandBarSection = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=30,
            buttons=self.buttons,
            prevent_dispatch_view = {False}
        )
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        self.info_pane_section.setup()
        self.command_bar_section.setup()
        
        # Prepare text for display in InfoPaneSection.
        if len(eng.game_state.team.members) > 0:
                self.instruction.text = "Press Enter to Embark on a Mission!"
                self.team_info.text = f"{len(eng.game_state.team.members)} Guild Members are ready to Embark!"
                self.instruction.label.color = arcade.color.GOLD
                self.team_info.label.color = arcade.color.GOLD
        else:
            self.instruction.text = "No Guild Members are assigned to a team!"
            self.instruction.label.color = arcade.color.RED_DEVIL
            self.team_info.text = "Assign Guild Members to a Team from the Roster before Embarking!"
            self.team_info.label.color = arcade.color.RED_DEVIL

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

    def on_draw(self) -> None:
        self.clear()

        if self.state == ViewStates.MISSIONS:
            for row in range(len(eng.game_state.mission_board.missions)):
                # self.selection is a user controlled value changed via up / down arrow keypress.
                # set opacity of the MissionCard border to visible if self.selection == the row being drawn.
                if self.selection.pos == row:
                    opacity = 255
                else:
                    opacity = 25

                # Controls size of reserved space beneath MissionCards.
                reserved_space = 75

                MissionCard(
                    width=WindowData.width,
                    height=WindowData.height,
                    mission=eng.game_state.mission_board.missions[row],
                    margin=self.margin,
                    opacity=opacity,
                    reserved_space=reserved_space,
                ).draw_card(row)

        if self.state == ViewStates.COMBAT:
            if eng.awaiting_input:
                self.combat_screen.draw_turn_prompt()

            if eng.mission_in_progress == False:
                self.combat_screen.draw_turn_prompt()

            self.combat_screen.draw_message()
            self.combat_screen.draw_stats()

    def on_update(self, delta_time: float) -> None:
        if self.state == ViewStates.COMBAT:
            hook = lambda: None
            if not eng.awaiting_input:
                hook = eng.next_combat_action

            self.combat_screen.on_update(delta_time=delta_time, hook=hook)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.L:
                self.instruction.label.color = arcade.color.GREEN
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    guild_view = GuildView()
                    self.window.show_view(guild_view)

            case arcade.key.DOWN:
                self.selection.decr()

            case arcade.key.UP:
                self.selection.incr()

            case arcade.key.RETURN:
                if len(eng.game_state.guild.team.members) > 0:
                    self.command_bar_section.enabled = False
                    self.info_pane_section.enabled = False
                    eng.selected_mission = self.selection.pos
                    eng.init_dungeon()

                    if not eng.game_state.dungeon.cleared:
                        eng.init_combat()
                        self.combat_screen = CombatScreen()

                        self.state = ViewStates.COMBAT
                        eng.await_input()

            case arcade.key.NUM_0 | arcade.key.KEY_0:
                if eng.awaiting_input:
                    eng.set_target(0)

            case arcade.key.NUM_1 | arcade.key.KEY_1:
                if eng.awaiting_input:
                    eng.set_target(1)

            case arcade.key.NUM_2 | arcade.key.KEY_2:
                if eng.awaiting_input:
                    eng.set_target(2)

            case arcade.key.SPACE:
                if eng.awaiting_input:
                    eng.next_combat_action()
                    eng.awaiting_input = False
