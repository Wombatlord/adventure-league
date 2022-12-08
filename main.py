import arcade
from src.gui.views import WindowData, TitleView

def start_adventure_league():
    """Startup"""
    window = arcade.Window(
        WindowData.width, WindowData.height, "Adventure League!", resizable=True
    )
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()

start_adventure_league()