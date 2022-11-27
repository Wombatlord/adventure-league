import arcade
from src.gui.mission_card import MissionCard
from src.engine.engine import scripted_run, eng
from dataclasses import dataclass
from arcade import Window

# class MainWindow(arcade.Window):
#     def __init__(self, width, height, title):
#         super().__init__(width, height, title, resizable=True)

#         self.width = width
#         self.height = height
#         self.title = title


@dataclass
class WindowData:
    width = 800
    height = 600
    title_background = arcade.load_texture("./background_glacial_mountains.png")
    mission_background = arcade.load_texture("./mb.png")
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
    def draw_panels(self):
        for col in range(2):
            x = (self.margin + WindowData.width) * col + self.margin + WindowData.width // 2
            arcade.draw_rectangle_outline(
                center_x=x / 2 - self.margin,
                center_y=WindowData.height * 0.5 + self.margin * 4,
                width=WindowData.width * 0.5 - self.margin * 4,
                height=WindowData.height - self.margin * 10,
                color=arcade.color.GOLDENROD,
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

                self.populate_roster_pane(x = x)

            if col == 1:
                arcade.Text(
                    "Team",
                    start_x=(x / 2) - self.margin,
                    start_y=WindowData.height - self.margin * 8,
                    font_name=WindowData.font,
                    font_size=25,
                    anchor_x="center",
                ).draw()
    
    def populate_roster_pane(self, x):
        """
        Print the name of each entity in a guild roster in a centralised column.
        """
        for merc in range(len(eng.guild.roster)):
                    y2 = (self.margin + WindowData.height) * merc + self.margin + WindowData.height // 2
                    arcade.Text(
                        f"{eng.guild.roster[merc].name.first_name.capitalize()}",
                        start_x=(x / 2) - self.margin * 2,
                        start_y=y2 * 0.05 + WindowData.height - self.margin * 25,
                        font_name=WindowData.font,
                        font_size=12,
                        anchor_x="center",
                    ).draw()

    def on_draw(self):
        self.clear()
        self.draw_panels()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            guild_view = GuildView()
            self.window.show_view(guild_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class MissionsView(arcade.View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.background = WindowData.mission_background
        self.margin = 5
        self.selection = 0

    def on_draw(self):
        self.clear()

        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowData.width, WindowData.height, self.background
        )

        for row in range(len(eng.mission_board.missions)):
            # self.selection is a user controlled value changed via up / down arrow keypress.
            # set opacity of the MissionCard border to visible if self.selection == the row being drawn.
            if self.selection == row:
                MissionCard(
                    width=WindowData.width,
                    height=WindowData.height,
                    mission=row,
                    margin=self.margin,
                    opacity=255,
                ).draw_card()
            else:
                MissionCard(
                    width=WindowData.width,
                    height=WindowData.height,
                    mission=row,
                    margin=self.margin,
                    opacity=25,
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
            if self.selection == 0:
                self.selection = 2

            else:
                self.selection -= 1

        if symbol == arcade.key.UP:
            if self.selection == len(eng.mission_board.missions) - 1:
                self.selection = 0

            else:
                self.selection += 1

        if symbol == arcade.key.RETURN:
            eng.selected_mission = self.selection
            scripted_run()


def start_adventure_league():
    """Startup"""
    # scripted_run()
    window = arcade.Window(
        WindowData.width, WindowData.height, "Adventure League!", resizable=True
    )
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()
