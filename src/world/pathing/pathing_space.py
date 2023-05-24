from __future__ import annotations

import random
from functools import lru_cache
from random import randint
from typing import Generator, Iterable, Sequence

from astar import AStar
from src.gui.biome_textures import BiomeName

from src.world.level.room_layouts import Terrain, TerrainNode
from src.world.node import Node


class PathingSpace(AStar):
    minima: Node
    maxima: Node

    @classmethod
    def from_level_geometry(cls, geometry: tuple[TerrainNode], floor_level=0):
        terrain = Terrain(geometry, [random.choice(BiomeName.all_biomes())]).with_biome_textures()
        block_locations = terrain.nodes
        all_traversable = []
        for n in block_locations:
            if n.z != floor_level - 1:
                continue

            if n.above in block_locations:
                continue

            all_traversable.append(n.above)

        minima = terrain.minima
        maxima = terrain.maxima

        exclusions = {
            Node(x, y, floor_level)
            for x in range(minima.x, maxima.x)
            for y in range(minima.y, maxima.y)
        } - {*all_traversable}

        return PathingSpace(minima, maxima, exclusions)

    def __init__(self, minima: Node, maxima: Node, exclusions: set[Node] | None = None):
        if exclusions is None:
            exclusions = set()

        self.minima = minima
        self.maxima = maxima
        self.static_exclusions = exclusions
        self.dynamic_exclusions = set()

    def __contains__(self, item: Node) -> bool:
        return self.in_bounds(item) and item not in self.exclusions

    @property
    def exclusions(self) -> set[Node]:
        return self.dynamic_exclusions | self.static_exclusions

    @exclusions.setter
    def exclusions(self, exc_set: set[Node]):
        self.dynamic_exclusions = exc_set

    def in_bounds(self, node: Node) -> bool:
        x_within = self.minima.x <= node.x < self.maxima.x
        y_within = self.minima.y <= node.y < self.maxima.y
        return x_within and y_within

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if candidate in self:
                yield candidate

    def distance_between(self, n1: Node, n2: Node) -> int:
        return 1 if sum(abs(delta) for delta in (n1 - n2)) == 1 else 1.5

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        return 1

    @property
    def height(self) -> int:
        return self.maxima.y - self.minima.y

    @property
    def width(self) -> int:
        return self.maxima.x - self.minima.x

    @property
    def dimensions(self) -> tuple[int, int]:
        return (self.width, self.height)

    def get_path(self, start: Node, finish: Node) -> tuple[Node, ...] | None:
        # we exclude all occupied nodes so any paths from occupied nodes (i.e. all combat pathfinding)
        # will need to have the start/end node added back to the pathing space temporarily
        deferred_restore = [
            start if start in self.dynamic_exclusions else False,
            finish if finish in self.dynamic_exclusions else False,
        ]
        for include in deferred_restore:
            if include:
                self._include(include)

        path = self.astar(start, finish)

        # after we've got the path, we make sure that if it wasn't in the space before we started
        # then it won't be after we return
        for exclude in deferred_restore:
            if exclude:
                self._exclude(exclude)

        if path is None:
            return

        return tuple(path)

    def _include(self, node: Node) -> None:
        self.dynamic_exclusions -= {node}  # idempotent remove from set

    def _exclude(self, node: Node) -> None:
        self.dynamic_exclusions.add(node)  # idempotent add to set

    def get_path_len(self, start: Node, end: Node) -> int | None:
        path = self.get_path(start, end)

        if path is None:
            return

        return len([*path])

    def choose_random_node(self, excluding: set[Node] = ()) -> Node:
        # if there are extra exclusions create a temp space with those exclusions as well as the pre-existing exclusions
        tmp_space = self
        if excluding:
            tmp_space = PathingSpace(
                self.minima, self.maxima, exclusions=self.exclusions | set(excluding)
            )

        def _try_node() -> Node:
            return Node(
                x=randint(tmp_space.minima.x, tmp_space.maxima.x),
                y=randint(tmp_space.minima.y, tmp_space.maxima.y),
            )

        while (node := _try_node()) not in tmp_space:
            continue

        return node

    def __len__(self):
        """
        The number of unoccupied nodes
        """
        return self.width * self.height - len(self.exclusions)

    def choose_next_unoccupied(self, start_at: Node) -> Node | None:
        """
        Does a random walk from the passed node. Returns the first unoccupied
        node encountered
        Args:
            start_at: The first node in the walk

        Returns: the first unoccupied node encountered, will be the passed node if
        it is unoccupied.

        """
        attempt = start_at

        if attempt in self:
            return attempt

        tried = {attempt}  # will be empty if node not excluded
        while (
            attempt := random.choice(
                [adj for adj in attempt.adjacent if self.in_bounds(adj)]
            )
        ) not in self:
            tried.add(attempt)
            # if we've tried every unique node
            if len(tried) == len(self):
                return

        return attempt

    @property
    def y_range(self) -> Iterable[int]:
        return range(self.minima.y, self.maxima.y)

    @property
    def x_range(self) -> Iterable[int]:
        return range(self.minima.x, self.maxima.x)

    def all_included_nodes(self, exclude_dynamic=True) -> Sequence[Node]:
        node_check = lambda x, y: Node(x, y) in self
        if not exclude_dynamic:
            node_check = lambda x, y: Node(x, y) not in self.static_exclusions

        return tuple(
            Node(x, y)
            for x in range(self.minima.x, self.maxima.x)
            for y in range(self.minima.y, self.maxima.y)
            if node_check(x, y)
        )

    def is_pathable(self, node: Node) -> bool:
        return self.in_bounds(node) and node not in self.static_exclusions


def pretty_path(space: PathingSpace, start: Node, end: Node) -> str:
    row = [" "] * space.width
    empty = [[*row] for _ in range(space.height)]

    for exclusion in space.exclusions:
        empty[exclusion.y][exclusion.x] = "X"

    for place in space.astar(start, end):
        empty[place.y][place.x] = "·"

    lines = map("".join, empty[::-1])

    return "\n".join(lines)
