from __future__ import annotations

import random
from functools import lru_cache
from random import randint
from typing import Any, Callable, Generator, Iterable, Protocol, Sequence, TypeVar

from astar import AStar

from src.gui.biome_textures import BiomeName
from src.world.level.room_layouts import Terrain, TerrainNode
from src.world.node import Node
from pyglet.math import Vec3
import abc

Item = TypeVar("Item", bound=object)


class Container(Protocol[Item]):
    def __contains__(self, item: Item):
        pass

class PathingStrategyInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        pass
    
    @abc.abstractmethod
    def distance_between(self, n1: Node, n2: Node) -> int:
        pass

    @abc.abstractmethod
    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        pass
    
    
class HeightMap:
    terrain: Terrain

    def __init__(self, terrain) -> None:
        self.terrain = terrain

    def __call__(self, node: Node) -> Node | None:
        return self.terrain.highest_node_at(node.x, node.y)


class FlatStrategy(PathingStrategyInterface):
    def __init__(self, all_nodes: Container[Node]) -> None:
        self.all_nodes = all_nodes

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if candidate in self.all_nodes:
                yield candidate

    def distance_between(self, n1: Node, n2: Node) -> int:
        return 1 if sum(abs(delta) for delta in (n1 - n2)) == 1 else 1.5

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        return 1


class HeightMapStrategy(PathingStrategyInterface):
    all_nodes: Container[Node]
    height_map: Callable[[Node], Node | None]

    def __init__(
        self, all_nodes: Container[Node], height_map: Callable[[Node], Node | None]
    ) -> None:
        self.all_nodes = all_nodes
        self.height_map = height_map

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if height_adjusted := self.height_map(candidate):
                yield height_adjusted

    def distance_between(self, n1: Node, n2: Node) -> int:
        aggregate_offset = sum(*(abs(component) for component in n1 - n2))
        match aggregate_offset:
            case 3:
                return 2
            case 2:
                return 1.5
            case 1:
                return 1
            case _:
                return 0

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        v1 = Vec3(*n1)
        v2 = Vec3(*n2)

        return v1.distance(v2)


class PathingSpace(AStar):
    minima: Node
    maxima: Node

    @classmethod
    def from_level_geometry(cls, geometry: tuple[TerrainNode], floor_level=0):
        terrain = Terrain(geometry)
        height_map = HeightMap(terrain=terrain)
        strat = HeightMapStrategy(
            all_nodes=[node.above for node in terrain.nodes], height_map=height_map
        )

        return PathingSpace(
            minima=terrain.minima, maxima=terrain.maxima, exclusions=set(), pathing_strategy=strat
        )

    def __init__(
        self,
        minima: Node,
        maxima: Node,
        exclusions: set[Node] | None = None,
        pathing_strategy: PathingStrategyInterface | None = None
    ):
        if exclusions is None:
            exclusions = set()

        self.minima = minima
        self.maxima = maxima
        self.static_exclusions = exclusions
        self.dynamic_exclusions = set()
        self.strat = pathing_strategy or FlatStrategy(self)

    def __contains__(self, item: Node) -> bool:
        return (
            self.in_bounds(item)
            and item not in self.exclusions
            and item in self.height_map
        )

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
        yield from self.strat.neighbors(node)

    def distance_between(self, n1: Node, n2: Node) -> int:
        return self.strat.distance_between(n1, n2)

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        return self.strat.heuristic_cost_estimate(n1, n2)

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
        try:
            while (
                attempt := random.choice(
                    [adj for adj in attempt.adjacent if self.in_bounds(adj)]
                )
            ) not in self:
                tried.add(attempt)
                # if we've tried every unique node
                if len(tried) == len(self):
                    return
        except IndexError as e:
            raise ValueError(
                f"Choose_next_unoccupied({start_at=}) was started at a location that is probably out of bounds"
            ) from e

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
