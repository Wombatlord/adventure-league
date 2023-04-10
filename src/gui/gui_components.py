from typing import Callable, NamedTuple

import arcade.color
from arcade.gui import UIImage, UISpriteWidget
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.widgets.text import UILabel

from src.config import font_sizes
from src.gui.gui_utils import ScrollWindow
from src.gui.window_data import WindowData
from src.textures.pixelated_nine_patch import PixelatedNinePatch, PixelatedTexture

Rgba = tuple[int, int, int, int]
Attach = Callable[[UILabel], UILabel]
Colored_Label = tuple[str, str, int, Rgba] | tuple[str, str, int, Rgba, Attach]
from PIL import Image


class ColoredLabel(NamedTuple):
    text: str
    align: str
    font_size: int
    colour: Rgba
    attach_observer: Attach = lambda *args: args[-1]

    def get_ui_label(
        self,
        width,
        size_hint: tuple[int, int] | None = None,
        height: int | None = None,
        multiline=False,
    ) -> UILabel:
        return self.attach_observer(
            UILabel(
                text=self.text,
                font_size=self.font_size,
                font_name=WindowData.font,
                width=width,
                height=height,
                multiline=multiline,
                align=self.align,
                size_hint=size_hint,
                text_color=self.colour,
            )
        )


Colored_Label_Pair = tuple[Colored_Label, Colored_Label]

Top_Right_Bottom_Left_Padding = tuple[int, int, int, int]


def label_with_observer(
    label: Colored_Label,
    width,
    height,
    align,
    font_size,
    color,
    attach,
    multiline,
):
    return ColoredLabel(label, align, font_size, color, attach).get_ui_label(
        width=width, height=height, multiline=multiline
    )


def box_containing_horizontal_label_pair(
    labels_with_colors: Colored_Label_Pair,
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
    space_between_labels: int = 6,
    width=None,
    size_hint=(None, None),
):
    return UIBoxLayout(
        vertical=False,
        height=35,
        size_hint=(1, None),
        children=map(
            lambda cl: cl.get_ui_label(width=width, size_hint=size_hint),
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


def create_colored_shadowed_UILabel_header(
    header_string: str, color: tuple[int, int, int, int], font_size=25, height=35
) -> tuple[UIWidget, UIWidget]:
    return (
        UILabel(
            text=f"{header_string}",
            width=WindowData.width,
            height=height,
            font_size=font_size,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=arcade.color.BLACK,
        ),
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
                font_size=font_sizes.BODY,
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
                font_size=font_sizes.BODY,
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


def get_mission_banner(banner_refs: list) -> list:
    with Image.open("assets\sprites\mission_banner.png") as banner_image:
        banner_refs.append(
            UIImage(
                texture=PixelatedTexture(image=banner_image),
                size_hint=(None, None),
                height=61,
                width=772,
            )
        )

    with Image.open("assets\sprites\mission_banner_dark.png") as banner_image:
        for _ in range(2):
            banner_refs.append(
                UIImage(
                    texture=PixelatedTexture(image=banner_image),
                    size_hint=(None, None),
                    height=61,
                    width=772,
                )
            )

    return banner_refs


def get_background_panel(panel_highlighted):
    return UIImage(
        texture=PixelatedNinePatch(
            left=15, right=15, bottom=15, top=15, texture=panel_highlighted
        ),
        size_hint=(1, 1 / 3),
    )


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
