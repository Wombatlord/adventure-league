import arcade

from src.engine.init_engine import eng
from src.gui.views import TitleView, WindowData


def start_adventure_league():
    """Startup"""
    window = arcade.Window(
        800, 600, "Adventure League!", resizable=True, fullscreen=False
    )
    window.set_icon(WindowData.window_icon)
    window.set_minimum_size(800, 600)
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()

start_adventure_league()