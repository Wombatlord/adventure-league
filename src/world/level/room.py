from functools import lru_cache

from src.world.isometry.transforms import draw_priority
from src.world.pathing.grid_utils import Node


@lru_cache(maxsize=1)
def basic_room(dimensions: tuple[int, int], height: int = 0) -> tuple[Node]:
    floor = [
        Node(x=x, y=y, z=height - 1)
        for x in range(dimensions[0])
        for y in range(dimensions[1])
    ]
    walls = (
        [Node(x=dimensions[0], y=y, z=height) for y in range(dimensions[1])]
        + [Node(x=x, y=dimensions[1], z=height) for x in range(dimensions[0])]
        + [
            Node(x=10, y=10, z=height),
            Node(x=10, y=10, z=height + 1),
        ]
    )

    return tuple(sorted(floor + walls, key=draw_priority))
