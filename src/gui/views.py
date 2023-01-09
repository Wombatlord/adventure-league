import arcade
from arcade import Window
from src.gui.window_data import WindowData
from src.gui.gui_utils import Cycle, ScrollWindow
from src.gui.mission_card import MissionCard
from src.gui.roster_view_components import (
    bottom_bar,
    draw_panels,
)
from src.engine.engine import scripted_run, eng

class TitleView(arcade.View):
    def __init__(self, window: Window = None):
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

    commands = ["[m]issions", "[r]oster", "[t]eam"]

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
            f"{eng.guild.name}",
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
        self.roster = eng.guild.roster
        self.team_members = eng.guild.team.members
        self.margin = 5
        self.col_select = Cycle(2)
        # self.roster_member_selection = Cycle(len(eng.guild.roster))
        # self.team_member_selection = Cycle(0, 0)
        self.row_height = 25
        self.roster_pane = 0
        self.team_pane = 1
        self.roster_scroll_window = ScrollWindow([], 0, 4)
        print(self.roster_scroll_window.visible_size)
        print(self.roster_scroll_window.stretch_limit)
        self.roster_scroll_window.init_items(self.roster)
        self.team_scroll_window = ScrollWindow([], 0, 4)
        self.team_scroll_window.init_items(self.team_members)


    def on_draw(self):
        self.clear()
        draw_panels(
            margin=self.margin,
            col_select=self.col_select,
            height=WindowData.height,
            width=WindowData.width,
            row_height=self.row_height,
            roster_scroll_window=self.roster_scroll_window,
            team_scroll_window=self.team_scroll_window
        )
        merc = None
        if self.col_select.pos == 0 and len(self.roster_scroll_window.items) > 0:
            merc = self.roster_scroll_window.items[self.roster_scroll_window.position.pos]
        
        if self.col_select.pos == 1 and len(self.team_scroll_window.items) > 0:
            merc = self.team_scroll_window.items[self.team_scroll_window.position.pos]

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

            case arcade.key.RIGHT:
                self.col_select.incr()

            case arcade.key.LEFT:
                self.col_select.decr()

            case arcade.key.UP:
                if self.col_select.pos == 0:
                    self.roster_scroll_window.decr_selection()
                    
                if self.col_select.pos == 1:
                    self.team_scroll_window.decr_selection()


            case arcade.key.DOWN:
                if self.col_select.pos == 0:
                    self.roster_scroll_window.incr_selection()

                if self.col_select.pos == 1:
                    self.team_scroll_window.incr_selection()
                

            case arcade.key.ENTER:
                if self.col_select.pos == self.roster_pane and len(self.roster_scroll_window.items) > 0:
                    # Move merc from ROSTER to TEAM. Increase Cycle.length for team, decrease Cycle.length for roster.
                    # Assign to Team & Remove from Roster.
                    self.team_scroll_window.append(self.roster_scroll_window.selection)
                    self.roster_scroll_window.pop()

                    # Update Engine state.
                    eng.guild.roster = self.roster_scroll_window.items
                    eng.guild.team.members = self.team_scroll_window.items

                if self.col_select.pos == self.team_pane and len(self.team_scroll_window.items) > 0:
                    # Move merc from TEAM to ROSTER
                    self.roster_scroll_window.append(self.team_scroll_window.selection)
                    
                    # Remove from Team array
                    self.team_scroll_window.pop()

                    # Update Engine state.
                    eng.guild.roster = self.roster_scroll_window.items
                    eng.guild.team.members = self.team_scroll_window.items


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

    def on_draw(self):
        self.clear()

        # arcade.draw_lrwh_rectangle_textured(
        #     0, 0, WindowData.width, WindowData.height, self.background
        # )

        for row in range(len(eng.mission_board.missions)):
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
                mission=eng.mission_board.missions[row],
                margin=self.margin,
                opacity=opacity,
                reserved_space=reserved_space,
            ).draw_card(row)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height

    # def on_update(self, delta_time: float):
    #     eng.process_action_queue()

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.DOWN:
                self.selection.decr()

            case arcade.key.UP:
                self.selection.incr()

            case arcade.key.RETURN:
                eng.selected_mission = self.selection.pos
                scripted_run()
