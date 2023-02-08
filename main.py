import arcade
from src.gui.views import WindowData, TitleView
from src.engine.init_engine import eng

def start_adventure_league():
    """Startup"""
    window = arcade.Window(
        WindowData.width, WindowData.height, "Adventure League!", resizable=True
    )
    window.set_icon(WindowData.window_icon)
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()

start_adventure_league()