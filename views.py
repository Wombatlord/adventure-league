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
    def __init__(self, window = None):
        super().__init__(window)
        self.background = arcade.load_texture("./bg.png")

    def on_show_view(self):
        """Called when switching to this view"""
        pass        

    def on_draw(self):
        """Draw the title screen"""
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0,
                                            WindowBounds.width, WindowBounds.height,
                                            self.background)
        arcade.draw_text(
            "ADVENTURE LEAGUE!",
            WindowBounds.width / 2,
            WindowBounds.height / 2,
            arcade.color.GOLDENROD,
            font_size=30,
            anchor_x="center",
        )

        arcade.draw_text(
            "Press G for a Guild View!",
            WindowBounds.width / 2,
            WindowBounds.height / 4,
            arcade.color.GOLDENROD,
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

    def bottom_bar(self):
        margin = 5

        arcade.draw_lrtb_rectangle_outline(
            left = margin,
            right = WindowBounds.width - margin,
            top = WindowBounds.height * 0.3,
            bottom=margin,
            color= arcade.color.GOLDENROD
        )

        guild_name = arcade.Text(
            f"{eng.guild.name}",
            WindowBounds.width / 2,
            WindowBounds.height * 0.3 - 25,
            anchor_x="center",
            color=arcade.color.GOLDENROD,
        )

        gap = int(WindowBounds.width /25)
        # print(gap)
        binds = (" " * gap) + "[m]issions" + (" " * gap) + "[r]oster" + (" " * gap) + "[t]eam"
        keys = arcade.Text(
            binds,
            margin,
            margin * 2,         
        )
        keys.draw()
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
            self.window.show_view(title_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowBounds.width = width
        WindowBounds.height = height


def main():
    """Startup"""
    scripted_run()
    window = arcade.Window(WindowBounds.width, WindowBounds.height, "Adventure League!", resizable=True)
    title_view = TitleView()
    window.show_view(title_view)
    arcade.run()


if __name__ == "__main__":
    main()
