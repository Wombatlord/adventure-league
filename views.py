import arcade
from engine import scripted_run, eng

WIDTH = 800
HEIGHT = 600

class TitleView(arcade.View):
    def on_show_view(self):
        """ Called when switching to this view"""
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        """ Draw the title screen """
        self.clear()
        arcade.draw_text("ADVENTURE LEAGUE!", WIDTH / 2, HEIGHT / 2,
                         arcade.color.GOLDENROD, font_size=30, anchor_x="center")

        arcade.draw_text("Press G for a Guild View!", WIDTH/2, HEIGHT/4, arcade.color.GOLDENROD, font_size=20, anchor_x="center")

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            guild_view = GuildView()
            self.window.show_view(guild_view)

class GuildView(arcade.View):
    """ Draw a view displaying information about a guild """
    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        guild_name = arcade.Text(f"{eng.guild.name}", WIDTH/2, HEIGHT/2, anchor_x="center", color=arcade.color.GOLDENROD)
        team_name = arcade.Text(f"{eng.guild.team.name}", WIDTH/2, HEIGHT/4, anchor_x="center", color=arcade.color.GOLDENROD)
        guild_name.draw()
        team_name.draw()
    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.G:
            title_view = TitleView()
            self.window.show_view(title_view)

def main():
    """ Startup """
    scripted_run()
    window = arcade.Window(WIDTH, HEIGHT, "Adventure League")
    title_view = TitleView()
    window.show_view(title_view)
    arcade.run()


if __name__ == "__main__":
    main()