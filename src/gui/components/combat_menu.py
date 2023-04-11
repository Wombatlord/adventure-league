from typing import Callable

from src.gui.components.menu import Menu
from src.utils.functional import in_sequence


def _title_case(s: str) -> str:
    return " ".join([word.capitalize() for word in s.split(" ")])


def build_from_event(
    event: dict,
    position: tuple[int, int],
    on_teardown: Callable[[], None] | None = None,
) -> Menu | None:
    if not (choices := event.get("choices")):
        return None

    if on_teardown is None:
        on_teardown = lambda: None

    menu_config = []

    # Top level menu: Move, Attack, Item etc.
    for action_type_name, available_actions in choices.items():
        # Specific actions of given type, say: Item -> Healing Potion
        sub_menu_config = []
        for option in available_actions:
            label = option.get("label", "MISSING LABEL")
            callback = option.get("on_confirm", lambda: print("MISSING CALLBACK"))
            sub_menu_item = (
                _title_case(label),
                in_sequence((callback, on_teardown)),
                True,
            )

            sub_menu_config.append(sub_menu_item)

        menu_config.append((_title_case(action_type_name), sub_menu_config))

    return Menu(menu_config=menu_config, pos=position, area=(250, 50))
