import arcade
window = arcade.Window(
    800, 600, "Adventure League!", resizable=True, fullscreen=False
)
from src.gui.views import WindowData, TitleView
from src.engine.init_engine import eng

def start_adventure_league():
    global window
    """Startup"""
    window.set_icon(WindowData.window_icon)
    window.set_minimum_size(800, 600)
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()

start_adventure_league()