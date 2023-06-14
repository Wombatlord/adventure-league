from __future__ import annotations

import random
from functools import lru_cache
from typing import NamedTuple, Self

from arcade import Texture

from src.gui.biome_textures import TileTypes
from src.tests.utils.proc_gen.test_wave_function_collapse import height_map
from src.world.isometry.transforms import draw_priority
from src.world.node import Node


class Terrain(NamedTuple):
    terrain_nodes: list[TerrainNode]

    @property
    def nodes(self):
        return [block.node for block in self.terrain_nodes]

    @property
    def in_plane(self, height) -> list[TerrainNode]:
        return [block for block in self.terrain_nodes if block.z == height]

    @property
    def minima(self) -> Node:
        min_x = min(block.node.x for block in self.terrain_nodes)
        min_y = min(block.node.y for block in self.terrain_nodes)

        return Node(min_x, min_y)

    @property
    def maxima(self) -> Node:
        max_x = max(block.node.x for block in self.terrain_nodes) + 1
        max_y = max(block.node.y for block in self.terrain_nodes) + 1

        return Node(max_x, max_y)


class TerrainNode:
    node: Node
    tile_type: int
    texture: Texture | None = None

    def __init__(self, node, tile_type) -> None:
        self.node = node
        self.tile_type = tile_type

    def __hash__(self) -> int:
        return hash(self.node)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, TerrainNode):
            return self.node == __value.node
        return False

    @classmethod
    def create(
        cls,
        x: int,
        y: int,
        z: int = 0,
        offset: Node = Node(0, 0),
        tile_type: int = TileTypes.FLOOR,
    ) -> Self:
        return cls(node=Node(x, y, z) + offset, tile_type=tile_type)


def rectangle(
    w: int = 1, h: int = 1, offset: Node = Node(0, 0)
) -> tuple[TerrainNode, ...]:
    return tuple(
        TerrainNode.create(x=x, y=y, offset=offset) for x in range(w) for y in range(h)
    )


@lru_cache(maxsize=1)
def basic_room(dimensions: tuple[int, int], height: int = 0) -> tuple[TerrainNode, ...]:
    floor = [
        TerrainNode.create(x, y, height - 1, tile_type=TileTypes.FLOOR)
        for x in range(dimensions[0])
        for y in range(dimensions[1])
    ]

    # walls = (
    #     [
    #         TerrainNode.create(x=dimensions[0], y=y, tile_type=TileTypes.WALL)
    #         for y in range(dimensions[1])
    #     ]
    #     + [
    #         TerrainNode.create(x=x, y=dimensions[1], z=height, tile_type=TileTypes.WALL)
    #         for x in range(dimensions[0])
    #     ]
    #     + [
    #         TerrainNode.create(
    #             x=dimensions[0], y=dimensions[1], z=height, tile_type=TileTypes.WALL
    #         ),
    #         TerrainNode.create(
    #             x=dimensions[0], y=dimensions[1], z=height + 1, tile_type=TileTypes.WALL
    #         ),
    #     ]
    # )

    # return tuple(sorted(floor + walls, key=draw_priority))

    return tuple(floor)


def basic_geography(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
    hm = height_map(*dimensions)
    print(hm)
    floor = [
        TerrainNode.create(x, y, hm[(x, y)].height * 0.3, tile_type=TileTypes.FLOOR)
        for x in range(dimensions[0])
        for y in range(dimensions[1])
    ]

    for n in floor:
        print(n.node)

    return tuple(floor)


@lru_cache(maxsize=1)
def side_pillars(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
    min_width = 5
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    w, h = dimensions
    pillars = [
        TerrainNode.create(x=x, y=y, tile_type=TileTypes.PILLAR)
        for x in range(1, w, 2)
        for y in (1, h - 2)
    ]
    return tuple(pillars + list(room))


@lru_cache(maxsize=1)
def alternating_big_pillars(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
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

    for pillar in pillars:
        pillar.tile_type = TileTypes.WALL

    return tuple(pillars + list(room))


@lru_cache(maxsize=1)
def one_big_pillar(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
    min_width = 10
    room = basic_room(dimensions, height)
    if min(dimensions[0], dimensions[1]) < min_width:
        return room

    pillars = [
        *rectangle(4, 4, offset=Node(3, 3)),
    ]

    return tuple(pillars + list(room))


@lru_cache(maxsize=1)
def one_block_corridor(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
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

    return tuple(pillars + list(room))


def test_layout(*args, **kwargs) -> tuple[TerrainNode, ...]:
    nodes = (Node(0, 0),)
    nodes += tuple([Node(x, 0) for x in range(1, 9)])
    nodes += tuple([Node(0, y) for y in range(1, 6)])
    nodes += tuple([Node(0, 0, z) for z in range(1, 3)])

    return tuple(TerrainNode.create(*node) for node in nodes)


def random_room(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
    return random.choice(
        [
            basic_room,
            side_pillars,
            alternating_big_pillars,
        ]
    )(dimensions, height)
