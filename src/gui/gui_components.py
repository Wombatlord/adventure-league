import arcade.color
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.text import UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

from src.gui.window_data import WindowData
from src.gui.gui_utils import ScrollWindow

Rgba = tuple[int, int, int, int]
Colored_Label = tuple[str, int, Rgba]
Colored_Label_Pair = tuple[Colored_Label, Colored_Label]

Top_Right_Bottom_Left_Padding = tuple[int, int, int, int]


def box_containing_horizontal_label_pair(
    labels_with_colors: Colored_Label_Pair,
    padding: Top_Right_Bottom_Left_Padding = (0, 0, 0, 0),
    space_between_labels: int = 6,
):
    box = UIBoxLayout(
        vertical=False,
        size_hint=(1, 0.3),
        space_between=space_between_labels,
    ).with_padding(top=padding[0], right=padding[1], bottom=padding[2], left=padding[3])

    label_pairs = map(
        lambda x: UILabel(
            text=x[0],
            font_size=x[1],
            align="left",
            size_hint=(None, None),
            text_color=x[2],
        ),
        labels_with_colors,
    )

    for label in label_pairs:
        box.add(label)

    return box

def create_colored_UILabel_header(
    header_string: str, color: tuple[int, int, int, int]
) -> UILabel:
    return UILabel(
        text=f"{header_string}",
        width=WindowData.width,
        height=50,
        font_size=25,
        font_name=WindowData.font,
        align="center",
        size_hint=(1, None),
        text_color=color,
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
                font_size=18,
                font_name=WindowData.font,
                align="center",
                size_hint=(0.75, None),
            ).with_border(color=arcade.color.GENERIC_VIRIDIAN),
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