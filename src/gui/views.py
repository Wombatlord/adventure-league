import arcade
import arcade.key
import arcade.color
from arcade import Window
from enum import Enum
from src.gui.window_data import WindowData
from src.gui.gui_utils import Cycle, ScrollWindow
from src.gui.mission_card import MissionCard
from src.gui.combat_screen import CombatScreen
from src.gui.roster_view_components import (
    bottom_bar,
    draw_panels,
    draw_recruiting_panel,
)
from src.engine.init_engine import eng

class ViewStates(Enum):
    ROSTER = "roster_view"
    RECRUIT = "recruit_view"
    MISSIONS = "missions_view"
    COMBAT = "combat_view"


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

    commands = ["[m]issions", "[r]oster", "[n]ew missions"]

    def bottom_bar(self):
        margin = 5

        arcade.draw_lrtb_rectangle_outline(
            left=margin,
            right=WindowData.width - margin,
            top=WindowData.height * 0.3,
            bottom=margin * 6,
            color=arcade.color.GOLDENROD,
        )

        guild_name = arcade.Text(
            f"{eng.game_state.guild.name}",
            WindowData.width / 2,
            WindowData.height * 0.3 - 25,
            anchor_x="center",
            color=arcade.color.GOLDENROD,
            font_name=WindowData.font,
        )

        for col in range(len(self.commands)):
            x = (margin + WindowData.width) * col + margin + WindowData.width // 2
            arcade.draw_rectangle_outline(
                center_x=x / 3 - margin,
                center_y=margin * 3,
                width=WindowData.width * 0.3,
                height=margin * 4,
                color=arcade.color.GOLDENROD,
            )

            arcade.Text(
                text=self.commands[col],
                start_x=(x / 3),
                start_y=margin * 2,
                anchor_x="center",
                font_name=WindowData.font,
            ).draw()

        guild_name.draw()

    def on_draw(self):
        self.clear()
        self.bottom_bar()

    def on_key_press(self, symbol: int, modifiers: int):

        match symbol:
            case arcade.key.G:
                title_view = TitleView()
                title_view.title_y = WindowData.height * 0.75
                title_view.start_y = WindowData.height * 0.3
                self.window.show_view(title_view)

            case arcade.key.N:
                if eng.game_state.mission_board is not None:
                    eng.game_state.mission_board.clear_board()
                    eng.game_state.mission_board.fill_board(max_enemies_per_room=3, room_amount=3)

            case arcade.key.M:
                missions_view = MissionsView()
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView()
                self.window.show_view(roster_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.recruitment_pool = eng.game_state.entity_pool.pool
        self.roster = eng.game_state.guild.roster
        self.team_members = eng.game_state.guild.team.members
        self.roster_limit = eng.game_state.guild.roster_limit
        self.margin = 5
        self.col_select = Cycle(2)
        self.row_height = 25
        self.roster_pane = 0
        self.team_pane = 1
        self.roster_scroll_window = ScrollWindow(self.roster, 10, 10)
        self.team_scroll_window = ScrollWindow(self.team_members, 10, 10)
        self.recruitment_scroll_window = ScrollWindow(self.recruitment_pool, 10, 10)
        self.state = ViewStates.ROSTER

    def on_draw(self):
        self.clear()
        merc = None
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
            if self.col_select.pos == 0 and len(self.roster_scroll_window.items) > 0:
                merc = self.roster_scroll_window.items[
                    self.roster_scroll_window.position.pos
                ]

            if self.col_select.pos == 1 and len(self.team_scroll_window.items) > 0:
                merc = self.team_scroll_window.items[
                    self.team_scroll_window.position.pos
                ]

        if self.state == ViewStates.RECRUIT:
            draw_recruiting_panel(
                margin=self.margin,
                height=WindowData.height,
                row_height=self.row_height,
                recruitment_scroll_window=self.recruitment_scroll_window,
            )

            if len(self.recruitment_scroll_window.items) > 0:
                merc = self.recruitment_scroll_window.items[
                    self.recruitment_scroll_window.position.pos
                ]

        bottom_bar(merc)

    def decr_col(self, col_count: int):
        self.col_select = (self.col_select - 1) % col_count

    def incr_col(self, col_count: int):
        self.col_select = (self.col_select + 1) % col_count

    def _log_input(self, symbol, modifiers):
        ...

    def _log_state(self):
        ...

    def on_key_press(self, symbol: int, modifiers: int):
        self._log_input(symbol, modifiers)

        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.R:
                if self.state == ViewStates.ROSTER:
                    self.recruitment_scroll_window = ScrollWindow(self.recruitment_pool, 10, 10)
                    self.state = ViewStates.RECRUIT

                elif self.state == ViewStates.RECRUIT:
                    self.roster_scroll_window = ScrollWindow(self.roster, 10, 10)
                    self.state = ViewStates.ROSTER

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
                
                elif self.state == ViewStates.RECRUIT:
                    self.recruitment_scroll_window.decr_selection()

            case arcade.key.DOWN:
                if self.state == ViewStates.ROSTER:
                    if self.col_select.pos == 0:
                        self.roster_scroll_window.incr_selection()

                    if self.col_select.pos == 1:
                        self.team_scroll_window.incr_selection()
                
                elif self.state == ViewStates.RECRUIT:
                    self.recruitment_scroll_window.incr_selection()

            case arcade.key.ENTER:
                if self.state == ViewStates.ROSTER:
                    if (
                        self.col_select.pos == self.roster_pane
                        and len(self.roster_scroll_window.items) > 0
                    ):
                        # Move merc from ROSTER to TEAM. Increase Cycle.length for team, decrease Cycle.length for roster.
                        # Assign to Team & Remove from Roster.
                        self.team_scroll_window.append(self.roster_scroll_window.selection)
                        eng.game_state.guild.team.assign_to_team(self.roster_scroll_window.selection)
                        self.roster_scroll_window.pop()

                        # Update Engine state.
                        self.roster = self.roster_scroll_window.items
                        eng.game_state.guild.roster = self.roster
                        self.team_members = self.team_scroll_window.items
                        eng.game_state.guild.team.members = self.team_members

                    if (
                        self.col_select.pos == self.team_pane
                        and len(self.team_scroll_window.items) > 0
                    ):
                        # Move merc from TEAM to ROSTER
                        self.roster_scroll_window.append(self.team_scroll_window.selection)

                        # Remove from Team array
                        self.team_scroll_window.pop()

                        # Update Engine state.
                        self.roster = self.roster_scroll_window.items
                        eng.game_state.guild.roster = self.roster
                        self.team_members = self.team_scroll_window.items
                        eng.game_state.guild.team.members = self.team_members
                
                elif self.state == ViewStates.RECRUIT:
                    if len(self.roster) + len(self.team_members) < self.roster_limit:
                        eng.recruit_entity_to_guild(self.recruitment_pool.index(self.recruitment_scroll_window.selection))
                        self.recruitment_scroll_window.pop()

        self._log_state()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class MissionsView(arcade.View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.background = WindowData.mission_background
        self.margin = 5
        self.selection = Cycle(
            3, 2
        )  # 3 missions on screen, default selected (2) is the top visually.
        self.state = ViewStates.MISSIONS
        self.combat_screen = CombatScreen()

    def on_draw(self):
        self.clear()

        # arcade.draw_lrwh_rectangle_textured(
        #     0, 0, WindowData.width, WindowData.height, self.background
        # )
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

    def on_update(self, delta_time: float):
        if self.state == ViewStates.COMBAT:

            hook = lambda: None
            if not eng.awaiting_input:
                hook = eng.next_combat_action

            self.combat_screen.on_update(delta_time=delta_time, hook=hook)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
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

            case arcade.key.M:
                if eng.mission_in_progress is False:
                    self.state = ViewStates.MISSIONS
