from typing import Callable, NamedTuple

import arcade.color
from arcade.gui import UIImage
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.widgets.text import UILabel

from src.gui.gui_utils import ScrollWindow
from src.gui.window_data import WindowData
from src.textures.pixelated_nine_patch import PixelatedNinePatch

Rgba = tuple[int, int, int, int]
Colored_Label = tuple[str, str, int, Rgba]


class ColoredLabel(NamedTuple):
    text: str
    align: str
    font_size: int
    colour: Rgba
    attach_observer: Callable[[UILabel], UILabel] = lambda *args: args[-1]


Colored_Label_Pair = tuple[Colored_Label, Colored_Label]

Top_Right_Bottom_Left_Padding = tuple[int, int, int, int]


def box_containing_horizontal_label_pair(
    labels_with_colors: Colored_Label_Pair,
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
    space_between_labels: int = 6,
    width=None,
    size_hint=(None, None),
):
    return UIBoxLayout(
        vertical=False,
        size_hint=(1, 0.2),
        children=map(
            lambda cl: cl.attach_observer(
                UILabel(
                    text=cl.text,
                    font_size=cl.font_size,
                    font_name=WindowData.font,
                    width=width,
                    align=cl.align,
                    size_hint=size_hint,
                    text_color=cl.colour,
                ),
            ),
            [ColoredLabel(*l) for l in labels_with_colors],
        ),
        space_between=space_between_labels,
    ).with_padding(top=padding[0], right=padding[1], bottom=padding[2], left=padding[3])


def create_colored_UILabel_header(
    header_string: str, color: tuple[int, int, int, int], font_size=25, height=35
) -> tuple[UIWidget]:
    return (
        UILabel(
            text=f"{header_string}",
            width=WindowData.width,
            height=height,
            font_size=font_size,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=color,
        ),
    )


def entity_labels_with_cost(scroll_window: ScrollWindow) -> tuple[UIWidget, ...]:
    """Returns a tuple of UILabels which can be attached to a UILayout

    Args:
        scroll_window (ScrollWindow): ScrollWindow containing an array of entities with names and costs.

    Returns:
        tuple[UIWidget]: Tuple of UILabels. Can simply be attached to the children parameter of a UILayout.
    """
    return tuple(
        map(
            lambda entity: UILabel(
                text=f"{entity.name.name_and_title}: {entity.cost} gp",
                width=WindowData.width,
                height=22,
                font_size=12,
                font_name=WindowData.font,
                align="center",
                size_hint=(0.75, None),
            ),  # .with_border(color=arcade.color.GENERIC_VIRIDIAN),
            scroll_window.items,
        )
    )


def entity_labels_names_only(scroll_window: ScrollWindow) -> tuple[UIWidget, ...]:
    """Returns a tuple of UILabels which can be attached to a UILayout

    Args:
        scroll_window (ScrollWindow): ScrollWindow containing an array of entities with names and costs.

    Returns:
        tuple[UIWidget]: Tuple of UILabels. Can simply be attached to the children parameter of a UILayout.
    """
    return tuple(
        map(
            lambda entity: UILabel(
                text=f"{entity.name.name_and_title}",
                width=WindowData.width,
                height=40,
                font_size=24,
                font_name=WindowData.font,
                align="center",
                size_hint=(1, None),
            ),  # .with_border(color=arcade.color.GENERIC_VIRIDIAN),
            scroll_window.items,
        )
    )


def vstack_of_three_boxes(
    bottom: int,
    height: int,
    content_top: tuple[UIWidget, ...],
    content_mid: tuple[UIWidget, ...],
    content_btm: tuple[UIWidget, ...],
) -> UIAnchorLayout:
    anchor = UIAnchorLayout(
        y=bottom,
        height=height,
        size_hint=(1, None),
    ).with_border(color=arcade.color.GOLD, width=5)

    for element, anchor_y in zip(
        [content_top, content_mid, content_btm],
        ["top", "center", "bottom"],
    ):
        anchor.add(
            anchor_x="center",
            anchor_y=anchor_y,
            child=UIBoxLayout(
                vertical=True,
                size_hint=(1, 1 / 3),
                children=element,
            ).with_border(color=arcade.color.ELECTRIC_BLUE, width=5),
        )

    return anchor


def single_box(
    bottom,
    height,
    children,
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
    vertical=True,
    border_width=5,
    panel=None,
) -> UIAnchorLayout:
    anchor = UIAnchorLayout(
        y=bottom,
        height=height,
        size_hint=(1, None),
    )  # .with_border(color=arcade.color.GOLD, width=border_width)

    if panel:
        anchor.add(
            child=UIImage(
                texture=PixelatedNinePatch(
                    left=15, right=15, bottom=15, top=15, texture=panel
                ),
                size_hint=(1, 1),
            )
        )

    anchor.add(
        child=UIBoxLayout(
            vertical=vertical,
            size_hint=(1, 1),
            children=children,
        ).with_padding(
            top=padding[0], right=padding[1], bottom=padding[2], left=padding[3]
        )
    )

    return anchor


def vertical_box_pair(
    bottom,
    height,
    top_content,
    bottom_content,
    top_size_hint=(1, 0.5),
    bottom_size_hint=(1, 0.5),
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
) -> UIAnchorLayout:
    anchor = UIAnchorLayout(
        y=bottom,
        height=height,
        size_hint=(1, None),
    ).with_border(color=arcade.color.GOLD, width=5)

    for anchor_y, element, size_hint in zip(
        ["top", "bottom"],
        [top_content, bottom_content],
        [top_size_hint, bottom_size_hint],
    ):
        anchor.add(
            anchor_y=anchor_y,
            child=UIBoxLayout(
                vertical=True,
                size_hint=size_hint,
                children=element,
            )
            .with_border(color=arcade.color.ELECTRIC_BLUE, width=0)
            .with_padding(
                top=padding[0], right=padding[1], bottom=padding[2], left=padding[3]
            ),
        )

    return anchor


def horizontal_box_pair(
    bottom,
    height,
    left_content,
    right_content,
    left_size_hint=(0.5, 1),
    right_size_hint=(0.5, 1),
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
    panel_highlighted=None,
    panel_darkened=None,
    tex_reference_buffer: list | None = None,
) -> UIAnchorLayout:
    if tex_reference_buffer is None:
        tex_reference_buffer = []

    anchor = UIAnchorLayout(
        y=bottom,
        height=height,
        size_hint=(1, None),
    ).with_border(color=arcade.color.GOLD, width=0)

    l = UIImage(
        texture=PixelatedNinePatch(
            left=15, right=15, bottom=15, top=15, texture=panel_highlighted
        ),
        size_hint=(0.5, 1),
    )
    r = UIImage(
        texture=PixelatedNinePatch(
            left=15, right=15, bottom=15, top=15, texture=panel_darkened
        ),
        size_hint=(0.5, 1),
    )

    tex_reference_buffer.extend([l, r])

    for panel, anchor_x in zip([l, r], ["left", "right"]):
        anchor.add(child=panel, anchor_x=anchor_x)

    for anchor_x, element, size_hint in zip(
        ["left", "right"],
        [left_content, right_content],
        [left_size_hint, right_size_hint],
    ):
        anchor.add(
            anchor_x=anchor_x,
            child=UIBoxLayout(
                vertical=True,
                size_hint=size_hint,
                children=element,
            ).with_padding(
                top=padding[0], right=padding[1], bottom=padding[2], left=padding[3]
            ),
        )

    return anchor
