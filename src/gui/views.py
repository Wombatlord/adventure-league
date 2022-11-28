import arcade
from src.gui.gui_utils import Cycle
from src.gui.mission_card import MissionCard
from src.engine.engine import scripted_run, eng
from dataclasses import dataclass
from arcade import Window
from typing import Sequence

@dataclass
class WindowData:
    width = 800
    height = 600
    title_background = arcade.load_texture("./assets/background_glacial_mountains.png")
    mission_background = arcade.load_texture("./assets/mb.png")
    font = "Alagard"


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
        if symbol == arcade.key.G:
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

    # def on_show_view(self):
    #     arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.bottom_bar()

        # team_name = arcade.Text(
        #     f"{eng.guild.team.name}",
        #     WindowBounds.width / 2,
        #     WindowBounds.height / 4,
        #     anchor_x="center",
        #     color=arcade.color.GOLDENROD,
        # )

        # team_name.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            title_view = TitleView()
            title_view.title_y = WindowData.height * 0.75
            title_view.start_y = WindowData.height * 0.3
            self.window.show_view(title_view)

        if symbol == arcade.key.M:
            missions_view = MissionsView()
            self.window.show_view(missions_view)

        if symbol == arcade.key.R:
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
        self.margin = 5
        self.col_select = Cycle(2)
        self.name_select = Cycle(len(self.roster))
        self.row_height = 500
        self.roster_pane = 0
        self.team_pane = 1

    def bottom_bar(self):
        margin = 5
        bar_height = 40
        arcade.draw_lrtb_rectangle_outline(
            left=margin * 2,
            right=WindowData.width - margin * 2,
            top=bar_height,
            bottom=margin,
            color=arcade.color.GOLDENROD,
        )

    def draw_panels(self):
        for col in range(2):
            """
            Derive a value for x positions based on the total width including margins,
            Multiply by the value of col to shift the position by a column width right,
            Add margin & window width for col * 0
            Divide this by 2 to get the halfway point with respect to width + margins
            """
            x = (self.margin + WindowData.width) * col + (
                self.margin + WindowData.width
            ) // 2

            """
            center_x: x / 2 positions center_x of the column at 1/4 of above x. ie, one column will fill half the vertical view.
            center_y: position center_y point slightly above halfway to leave space at the bottom.
            width: half the total window width with some adjustment by margin amounts.
            height: column is the full height of the window minus some adjustment by margin amounts.
            """
            if self.col_select.pos == col:
                arcade.draw_rectangle_outline(
                    center_x=x / 2 - self.margin / 2,
                    center_y=WindowData.height * 0.5 + self.margin * 4,
                    width=WindowData.width * 0.5 - self.margin * 4,
                    height=WindowData.height - self.margin * 10,
                    color=(218, 165, 32, 255),
                )

            if col == 0:
                arcade.Text(
                    "Roster",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=WindowData.height - self.margin * 8,
                    font_name=WindowData.font,
                    font_size=25,
                    anchor_x="center",
                ).draw()

                self.populate_roster_pane(x=x, col=self.col_select.pos)

            if col == 1:
                arcade.Text(
                    "Team",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=WindowData.height - self.margin * 8,
                    font_name=WindowData.font,
                    font_size=25,
                    anchor_x="center",
                ).draw()

                self.populate_team_pane(x=x, col=self.col_select.pos)

    
    def gen_heights(self, desc: bool = True) -> Sequence[int]:
        
        start = 2 * self.margin + WindowData.height + WindowData.height // 2
        incr = abs(self.row_height) # Negative indicates down
        if desc:
            incr = - abs(incr)

        current = start
        while True:
            yield current

            # increment on subsequent calls
            current = current + incr


    def populate_roster_pane(self, x, col):
        """
        Print the name of each entity in a guild roster in a centralised column.
        We pass x through from the calling scope to center text relative to the column width.
        """
        height = self.gen_heights()
        for merc in range(len(eng.guild.roster)):
            y2 = next(height)
            if col == 0 and merc == self.name_select.pos:
                arcade.Text(
                    f"{eng.guild.roster[merc].name.first_name.capitalize()} {merc}",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=y2 * 0.05 + WindowData.height - self.margin * 25,
                    font_name=WindowData.font,
                    font_size=12,
                    anchor_x="center",
                    color=(218, 165, 32, 255),
                ).draw()

            else:
                arcade.Text(
                    f"{eng.guild.roster[merc].name.first_name.capitalize()} {merc}",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=y2 * 0.05 + WindowData.height - self.margin * 25,
                    font_name=WindowData.font,
                    font_size=12,
                    anchor_x="center",
                    color=arcade.color.WHITE,
                ).draw()

    def populate_team_pane(self, x, col):
        """
        Print the name of each entity assigned to the team in a centralised column.
        We pass x through from the calling scope to center text relative to the column width.
        """
        height = self.gen_heights()
        for merc in range(len(eng.guild.team.members)):
            y2 = next(height)
            if col == 1 and merc == self.name_select.pos:
                arcade.Text(
                    f"{eng.guild.team.members[merc].name.first_name.capitalize()} {merc}",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=y2 * 0.05 + WindowData.height - self.margin * 25,
                    font_name=WindowData.font,
                    font_size=12,
                    anchor_x="center",
                    color=(218, 165, 32, 255),
                ).draw()

            else:
                arcade.Text(
                    f"{eng.guild.team.members[merc].name.first_name.capitalize()} {merc}",
                    start_x=(x / 2) - self.margin * 2,
                    start_y=y2 * 0.05 + WindowData.height - self.margin * 25,
                    font_name=WindowData.font,
                    font_size=12,
                    anchor_x="center",
                    color=arcade.color.WHITE,
                ).draw()

    def on_draw(self):
        self.clear()
        self.draw_panels()
        self.bottom_bar()

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

        if symbol == arcade.key.G:
            guild_view = GuildView()
            self.window.show_view(guild_view)

        # Cycle left or right in Roster & Team columns.
        if symbol == arcade.key.LEFT:
            self.col_select.decr()

        if symbol == arcade.key.RIGHT:
            self.col_select.incr()

        # Cycle up or down through Roster names
        if symbol == arcade.key.UP:
           self.name_select.decr()

        if symbol == arcade.key.DOWN:
           self.name_select.incr()

        if symbol == arcade.key.ENTER:
            if self.col_select.pos == self.roster_pane:
                eng.guild.team.assign_to_team(eng.guild.roster, self.name_select.pos)
                eng.guild.remove_from_roster(self.name_select.pos)

            if self.col_select.pos == self.team_pane:
                eng.guild.team.move_to_roster(self.name_select.pos)

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
        self.selection = Cycle(3, 2)

    def on_draw(self):
        self.clear()

        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowData.width, WindowData.height, self.background
        )

        for row in range(len(eng.mission_board.missions)):
            # self.selection is a user controlled value changed via up / down arrow keypress.
            # set opacity of the MissionCard border to visible if self.selection == the row being drawn.
            if self.selection.pos == row:
                opacity = 255
            else:
                opacity = 25
            
            MissionCard(
                width=WindowData.width,
                height=WindowData.height,
                mission=row,
                margin=self.margin,
                opacity=opacity,
            ).draw_card()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            guild_view = GuildView()
            self.window.show_view(guild_view)

        if symbol == arcade.key.DOWN:
            self.selection.decr()

        if symbol == arcade.key.UP:
            self.selection.incr()

        if symbol == arcade.key.RETURN:
            eng.selected_mission = self.selection
            scripted_run()
