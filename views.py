import arcade
from engine import scripted_run, eng
from dataclasses import dataclass

WIDTH = 800
HEIGHT = 600


# class MainWindow(arcade.Window):
#     def __init__(self, width, height, title):
#         super().__init__(width, height, title, resizable=True)

#         self.width = width
#         self.height = height
#         self.title = title


@dataclass
class WindowBounds:
    width = 800
    height = 600


class TitleView(arcade.View):
    def __init__(self, window=None):
        super().__init__(window)
        self.background = arcade.load_texture("./background_glacial_mountains.png")
        self.font = "Alagard"
        self.title_x = WindowBounds.width / 2
        self.title_y = -10

    def on_show_view(self):
        """Called when switching to this view"""
        pass

    def on_update(self, delta_time: float):
        if self.title_y < WindowBounds.height * 0.75:
            self.title_y += 5


    def on_draw(self):
        """Draw the title screen"""
        self.clear()
        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowBounds.width, WindowBounds.height, self.background
        )

        arcade.draw_text(
            "ADVENTURE LEAGUE!",
            self.title_x,
            self.title_y,
            arcade.color.GOLD,
            font_name=self.font,
            font_size=40,
            anchor_x="center",
        )

        arcade.draw_text(
            "Press G for a Guild View!",
            WindowBounds.width / 2,
            WindowBounds.height * 0.3,
            arcade.color.GOLDENROD,
            font_name=self.font,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            guild_view = GuildView()
            self.window.show_view(guild_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowBounds.width = width
        WindowBounds.height = height


class GuildView(arcade.View):
    """Draw a view displaying information about a guild"""

    command_cols = 3

    def bottom_bar(self):
        margin = 5

        arcade.draw_lrtb_rectangle_outline(
            left=margin,
            right=WindowBounds.width - margin,
            top=WindowBounds.height * 0.3,
            bottom=margin * 6,
            color=arcade.color.GOLDENROD,
        )

        guild_name = arcade.Text(
            f"{eng.guild.name}",
            WindowBounds.width / 2,
            WindowBounds.height * 0.3 - 25,
            anchor_x="center",
            color=arcade.color.GOLDENROD,
            font_name="Alagard",
        )

        for col in range(self.command_cols):
            coms = ["[m]issions", "[r]oster", "[t]eam"]
            x = (margin + WindowBounds.width) * col + margin + WindowBounds.width // 2
            arcade.draw_rectangle_outline(
                center_x=x / 3 - margin,
                center_y=margin * 3,
                width=WindowBounds.width * 0.3,
                height=margin * 4,
                color=arcade.color.GOLDENROD,
            )

            arcade.Text(coms[col], (x / 3) , margin * 2, anchor_x='center').draw()

        # gap = int(WindowBounds.width / 25)
        # # print(gap)
        # binds = (
        #     (" " * gap)
        #     + "[m]issions"
        #     + (" " * gap)
        #     + "[r]oster"
        #     + (" " * gap)
        #     + "[t]eam"
        # )
        # keys = arcade.Text(
        #     binds,
        #     margin,
        #     margin * 2,
        # )
        # keys.draw()
        guild_name.draw()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

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
            title_view.title_y = WindowBounds.height * 0.75
            self.window.show_view(title_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowBounds.width = width
        WindowBounds.height = height


def main():
    """Startup"""
    scripted_run()
    window = arcade.Window(
        WindowBounds.width, WindowBounds.height, "Adventure League!", resizable=True
    )
    title_view = TitleView()
    window.show_view(title_view)
    arcade.run()


if __name__ == "__main__":
    main()
