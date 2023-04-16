from arcade.gui import UIAnchorLayout, UIBoxLayout, UIWidget

from src.gui.components.layouts import get_background_panel, get_pixelated_tex_panel
from src.textures.pixelated_nine_patch import PixelatedNinePatch


def get_mission_banner(banner_refs: list) -> list:
    banner_refs.extend(
        get_pixelated_tex_panel(
            [
                "assets/sprites/mission_banner.png",
                "assets/sprites/mission_banner_dark.png",
                "assets/sprites/mission_banner_dark.png",
            ]
        )
    )

    return banner_refs


def mission_boxes(
    bottom: int,
    height: int,
    content_top: tuple[UIWidget, ...],
    content_mid: tuple[UIWidget, ...],
    content_btm: tuple[UIWidget, ...],
    panel_highlighted: PixelatedNinePatch,
    panel_darkened: PixelatedNinePatch,
    tex_reference_buffer: list | None = None,
    banner_reference_buffer: list | None = None,
) -> UIAnchorLayout:
    anchor = UIAnchorLayout(
        y=bottom,
        height=height,
        size_hint=(1, None),
    )

    if tex_reference_buffer is None:
        tex_reference_buffer = []

    # Prepare and add the texture backgrounds to the mission cards.
    top_panel = get_background_panel(panel_highlighted)
    center_panel = get_background_panel(panel_darkened)
    bottom_panel = get_background_panel(panel_darkened)

    tex_reference_buffer.extend([top_panel, center_panel, bottom_panel])

    for panel, anchor_y in zip(tex_reference_buffer, ["top", "center", "bottom"]):
        anchor.add(child=panel, anchor_y=anchor_y)

    ### WIP Mission Banner
    # Adds a BoxLayout overlapping with the BoxLayout for labels to allow drawing mission_banner behind mission header label
    # with correct alignments.
    if banner_reference_buffer is None:
        banner_reference_buffer = []

    banner_reference_buffer = get_mission_banner(banner_refs=banner_reference_buffer)

    for element, anchor_y in zip(
        banner_reference_buffer,
        ["top", "center", "bottom"],
    ):
        anchor.add(
            anchor_x="center",
            anchor_y=anchor_y,
            child=UIBoxLayout(
                vertical=True,
                # height=122,
                size_hint=(1, 0.335),
                children=[element],
                space_between=0,
            ).with_padding(top=10),
        )
    ### WIP Mission Banner

    # DROP SHADOW UILABELS
    for element, anchor_y in zip(
        [content_top[0], content_mid[0], content_btm[0]],
        ["top", "center", "bottom"],
    ):
        anchor.add(
            anchor_x="center",
            anchor_y=anchor_y,
            child=UIBoxLayout(
                vertical=True,
                # height=122,
                size_hint=(1, 0.33),
                children=[element],
                space_between=0,
            ).with_padding(top=26, right=1),
        )

    # COLORED UILABELS
    for element, anchor_y in zip(
        [content_top[1:], content_mid[1:], content_btm[1:]],
        ["top", "center", "bottom"],
    ):
        anchor.add(
            anchor_x="center",
            anchor_y=anchor_y,
            child=UIBoxLayout(
                vertical=True,
                # height=122,
                size_hint=(1, 0.33),
                children=element,
                space_between=0,
            ).with_padding(top=25),
        )

    return anchor
