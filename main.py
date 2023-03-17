import sys

import arcade

import src.engine.init_engine as _
from src.gui.views import TitleView, WindowData


def start_adventure_league():
    """Startup"""
    window = arcade.Window(
        WindowData.width, WindowData.height, "Adventure League!", resizable=True, fullscreen=False
    )
    
    window.set_icon(WindowData.window_icon)
    window.set_minimum_size(800, 600)
    title_view = TitleView(window=window)
    window.show_view(title_view)
    arcade.run()


if len(sys.argv) > 1 and sys.argv[1] == "S":
    from src.utils.sprites import sprite_viewer
    sprite_viewer.main()
else:
    start_adventure_league()
