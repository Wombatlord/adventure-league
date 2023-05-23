from __future__ import annotations

import random
from functools import lru_cache
from typing import NamedTuple, Self

from arcade import Texture

from src.textures.texture_data import SpriteSheetSpecs
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
        max_x = max(block.node.x for block in self.terrain_nodes)
        max_y = max(block.node.y for block in self.terrain_nodes)
        
        return Node(max_x, max_y)
    
    def highest_node_at(self, x,y) -> Node | None:
        nodes = [block.node for block in self.terrain_nodes if block.node.x == x and block.node.y == y]
        if not nodes:
            return None
        
        height_ordered = sorted(nodes, key=lambda n: -n.z)
        return height_ordered[0]
        
class TerrainNode(NamedTuple):
    node: Node
    material: Texture
    materials = [SpriteSheetSpecs.tiles.loaded[89], SpriteSheetSpecs.tiles.loaded[88]]

    @classmethod
    def create(cls, x, y, z=0, offset = Node(0,0)) -> Self:
        return cls(node=Node(x, y, z) + offset, material=random.choice(cls.materials))


def rectangle(
    w: int = 1, h: int = 1, offset: Node = Node(0, 0)
) -> tuple[TerrainNode, ...]:
    return tuple(TerrainNode.create(x=x, y=y, offset=offset)for x in range(w) for y in range(h))


@lru_cache(maxsize=1)
def basic_room(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode, ...]:
    floor = [
        TerrainNode.create(x, y, height - 1)
        for x in range(dimensions[0])
        for y in range(dimensions[1])
    ]

    walls = (
        [TerrainNode.create(x=dimensions[0], y=y) for y in range(dimensions[1])]
        + [
            TerrainNode.create(x=x, y=dimensions[1], z=height)
            for x in range(dimensions[0])
        ]
        + [
            TerrainNode.create(x=10, y=10, z=height),
            TerrainNode.create(x=10, y=10, z=height + 1),
        ]
    )

    return tuple(sorted(floor + walls, key=draw_priority))


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
        TerrainNode.create(x=x, y=y) for x in range(1, w, 2) for y in (1, h - 2)
    ]
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


def random_room(
    dimensions: tuple[int, int], height: int = 0
) -> tuple[TerrainNode]:
    return random.choice(
        [
            # basic_room,
            side_pillars,
            alternating_big_pillars,
        ]
    )(dimensions, height)
