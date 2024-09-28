from typing import Callable, NamedTuple

import arcade
from arcade.gui import UIAnchorLayout, UIBoxLayout, UIImage, UILabel, UIWidget
from PIL import Image

from src.gui.window_data import WindowData
from src.textures.pixelated_nine_patch import (PixelatedNinePatch,
                                               PixelatedTexture)


def get_background_panel(panel_highlighted):
    return UIImage(
        texture=PixelatedNinePatch(
            left=15, right=15, bottom=15, top=15, texture=panel_highlighted
        ),
        size_hint=(1, 1 / 3),
    )


def get_pixelated_tex_panel(paths: list[str]) -> list[UIImage]:
    ui_images = []
    for path in paths:
        with Image.open(path) as banner_image:
            ui_images.append(
                UIImage(
                    texture=PixelatedTexture(image=banner_image),
                    size_hint=(None, None),
                    height=61,
                    width=772,
                )
            )

    return ui_images


Rgba = tuple[int, int, int, int]
Attach = Callable[[UILabel], UILabel]
Colored_Label = tuple[str, str, int, Rgba] | tuple[str, str, int, Rgba, Attach]
Colored_Label_Pair = tuple[Colored_Label, Colored_Label]

Top_Right_Bottom_Left_Padding = tuple[int, int, int, int]


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


def get_colored_label(
    label: Colored_Label,
    width,
    height,
    align,
    font_size,
    color,
    attach,
    multiline,
) -> UILabel:
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
