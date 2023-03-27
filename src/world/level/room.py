import random
from functools import lru_cache

from src.world.isometry.transforms import draw_priority
from src.world.node import Node


def rectangle(w: int = 1, h: int = 1, offset: Node = Node(0, 0)) -> tuple[Node, ...]:
    return tuple(Node(x, y) + offset for x in range(w) for y in range(h))


@lru_cache(maxsize=1)
def basic_room(dimensions: tuple[int, int], height: int = 0) -> tuple[Node, ...]:
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


@lru_cache(maxsize=1)
def side_pillars(dimensions: tuple[int, int], height: int = 0) -> tuple[Node, ...]:
    min_width = 5
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    w, h = dimensions
    pillars = [Node(x, y) for x in range(1, w, 2) for y in (1, h - 2)]

    return tuple(sorted(pillars + list(room), key=draw_priority))


@lru_cache(maxsize=1)
def alternating_big_pillars(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[Node, ...]:
    min_width = 10
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    pillars = [
        *rectangle(2, 2, offset=Node(4, 1)),
        *rectangle(2, 2, offset=Node(4, 7)),
        *rectangle(2, 2, offset=Node(1, 4)),
        *rectangle(2, 2, offset=Node(7, 4)),
    ]

    return tuple(sorted(pillars + list(room), key=draw_priority))


@lru_cache(maxsize=1)
def one_big_pillar(dimensions: tuple[int, int], height: int = 0) -> tuple[Node, ...]:
    min_width = 10
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    pillars = [
        *rectangle(4, 4, offset=Node(3, 3)),
    ]

    return tuple(sorted(pillars + list(room), key=draw_priority))


@lru_cache(maxsize=1)
def one_block_corridor(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[Node, ...]:
    """
    Used as a stress test for congested pathing scenarios,
    not included in random room
    Args:
        dimensions:
        height:

    Returns:

    """
    min_width = 10
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    pillars = [
        *rectangle(10, 4, offset=Node(0, 0)),
        *rectangle(10, 4, offset=Node(0, 6)),
    ]

    return tuple(sorted(pillars + list(room), key=draw_priority))


def random_room(dimensions: tuple[int, int], height: int = 0) -> tuple[Node]:
    return random.choice(
        [
            basic_room,
            side_pillars,
            alternating_big_pillars,
        ]
    )(dimensions, height)
