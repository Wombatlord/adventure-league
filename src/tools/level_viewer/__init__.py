import arcade

from src.gui.window_data import WindowData
from src.tools.level_viewer.model.viewer_state import register_layout
from src.tools.level_viewer.ui.layout import LayoutView


def start(_: list[str]):
    """Startup"""
    window = arcade.Window(
        WindowData.width,
        WindowData.height,
        "Level Viewer",
        resizable=True,
        fullscreen=False,
    )

    window.set_icon(WindowData.window_icon)
    window.set_minimum_size(1600, 900)
    from src.world.level import room_layouts

    register_layout(room_layouts.alternating_big_pillars)
    register_layout(room_layouts.basic_room)
    register_layout(room_layouts.one_big_pillar)
    register_layout(room_layouts.one_block_corridor)
    register_layout(room_layouts.side_pillars)
    register_layout(room_layouts.random_room)
    title_view = LayoutView()
    window.show_view(title_view)

    # load wordlists
    arcade.run()
