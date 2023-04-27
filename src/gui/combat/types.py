from typing import Callable, NamedTuple

from src.world.node import Node


class Highlighter(NamedTuple):
    clear: Callable[[], None]
    highlight: Callable[[list[Node], list[Node], list[Node]], None]
    enable: Callable[[], None]
    disable: Callable[[], None]
