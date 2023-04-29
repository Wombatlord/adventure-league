from arcade.gui import UILabel, UIWidget

from src.config import font_sizes
from src.gui.components.scroll_window import ScrollWindow
from src.gui.window_data import WindowData


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
                text=f"{entity.name.name_and_title}: {entity.fighter.role.value.capitalize()}: {entity.cost} gp",
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
