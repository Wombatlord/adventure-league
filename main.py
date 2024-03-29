import sys

import arcade

import src.engine.init_engine as _
from src import config
from src.gui.title import TitleView
from src.gui.window_data import WindowData
from src.utils.proc_gen import constraints


def start_adventure_league():
    """Startup"""
    window = arcade.Window(
        WindowData.width,
        WindowData.height,
        "Adventure League!",
        resizable=True,
        fullscreen=False,
    )

    window.set_icon(WindowData.window_icon)
    window.set_minimum_size(1600, 900)
    title_view = TitleView(window=window)
    window.show_view(title_view)

    # load wordlists
    constraints.load()
    arcade.run()


if len(sys.argv) > 2 and sys.argv[1] == "-m":
    match sys.argv[2]:
        case "S":
            from src.utils.sprites import sprite_viewer

            sprite_viewer.main()

        case "D":
            config.DEBUG = True
            start_adventure_league()

else:
    start_adventure_league()
