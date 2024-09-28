from __future__ import annotations

import functools
import random
from random import randint
from typing import (TYPE_CHECKING, Any, Callable, Generator, Iterable,
                    NamedTuple, Self, Sequence)

from astar import AStar

from src.world.level.room_layouts import Z_INCR, Terrain
from src.world.pathing.pathing_strategy import (DefaultStrategy,
                                                HeightMapStrategy,
                                                PathingStrategy)

if TYPE_CHECKING:
    pass

from src.world.node import Node


def _flat(n: Node) -> Node:
    return Node(*n[:2])


def _flattened(f: Callable[[Node, ...], Any]) -> Callable[[Node, ...], Any]:
    @functools.wraps(f)
    def decorated(*nodes):
        return f(*[_flat(n) if isinstance(n, Node) else n for n in nodes])

    return decorated


class PathingSpace(AStar):
    minima: Node
    maxima: Node
    strategy: PathingStrategy

    @classmethod
    def from_terrain(cls, terrain: Terrain, floor_level=0):
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

    @classmethod
    def from_nodes(cls, level_geom: Sequence[Node], use_height_map: bool = False):
        minima = Node(
            min(n.x for n in level_geom),
            min(n.y for n in level_geom),
        )
        maxima = Node(
            max(n.x for n in level_geom) + 1,
            max(n.y for n in level_geom) + 1,
        )

        included = []

        if use_height_map:
            for n in level_geom:
                included.append(_flat(n))
            space = PathingSpace(minima, maxima, {*()})

            def height_map(n_: Node) -> float:
                col = [node for node in level_geom if node[:2] == n_[:2]]
                top = sorted(col, key=lambda node: node.z)[-1]
                height = top.above.z

                return height

            space.set_strategy(HeightMapStrategy(space, Z_INCR * 2, height_map))

        else:
            ground = {
                Node(x, y)
                for x in range(minima.x, maxima.x)
                for y in range(minima.y, maxima.y)
            }
            pits = {n for n in ground if n.below not in level_geom}
            walls = {n for n in ground if n in level_geom}
            excluded = pits | walls

            space = PathingSpace(minima, maxima, excluded)

        return space

    def __init__(
        self,
        minima: Node,
        maxima: Node,
        exclusions: set[Node] | None = None,
        strategy: PathingStrategy = None,
    ):
        if exclusions is None:
            exclusions = set()

        self.strategy = strategy or DefaultStrategy(self)

        self.minima = minima
        self.maxima = maxima
        self.static_exclusions = {_flat(n) for n in exclusions}
        self.dynamic_exclusions = set()

    def set_strategy(self, strat: PathingStrategy):
        self.strategy = strat

    def astar(self, start: Node, goal: Node) -> Iterable[Node] | None:
        path = super().astar(start, goal)
        return [self.strategy.to_level_position(n) for n in path]

    @_flattened
    def __contains__(self, item: Node) -> bool:
        return self.in_bounds(item) and item not in self.exclusions

    @property
    def exclusions(self) -> set[Node]:
        return self.dynamic_exclusions | self.static_exclusions

    @exclusions.setter
    def exclusions(self, exc_set: set[Node]):
        self.dynamic_exclusions = {_flat(n) for n in exc_set}

    @_flattened
    def in_bounds(self, node: Node) -> bool:
        x_within = self.minima.x <= node.x < self.maxima.x
        y_within = self.minima.y <= node.y < self.maxima.y
        return x_within and y_within

    @_flattened
    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        return self.strategy.neighbors(node)

    @_flattened
    def distance_between(self, n1: Node, n2: Node) -> int:
        return self.strategy.distance_between(n1, n2)

    @_flattened
    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int | float:
        return self.strategy.heuristic_cost_estimate(n1, n2)

    @property
    def height(self) -> int:
        return self.maxima.y - self.minima.y

    @property
    def width(self) -> int:
        return self.maxima.x - self.minima.x

    @property
    def dimensions(self) -> tuple[int, int]:
        return (self.width, self.height)

    @_flattened
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

        path = None
        try:
            path = self.astar(start, finish)
        except Exception as error:
            print(
                f"Astar couldn't resolve path for:\n"
                f"{start=}\n"
                f"{finish=}\n"
                f"{error=}\n"
            )
            pass

        # after we've got the path, we make sure that if it wasn't in the space before we started
        # then it won't be after we return
        for exclude in deferred_restore:
            if exclude:
                self._exclude(exclude)

        if path is None:
            return

        return tuple(path)

    @_flattened
    def _include(self, node: Node) -> None:
        self.dynamic_exclusions -= {node}  # idempotent remove from set

    @_flattened
    def _exclude(self, node: Node) -> None:
        self.dynamic_exclusions.add(node)  # idempotent add to set

    @_flattened
    def get_path_len(self, start: Node, end: Node) -> int | None:
        path = self.get_path(start, end)

        if path is None:
            return

        return len([*path])

    def choose_random_node(self, excluding: set[Node] = ()) -> Node:
        # if there are extra exclusions create a temp space with those exclusions as well as the pre-existing exclusions
        excluding = {_flat(n) for n in excluding}
        possible = {*self.all_included_nodes(exclude_dynamic=True)} - excluding
        if not possible:
            raise RuntimeError("The level is full")
        node = random.choice([*possible])
        return self.strategy.to_level_position(node)

    def __len__(self):
        """
        The number of unoccupied nodes
        """
        return self.width * self.height - len(self.exclusions)

    @_flattened
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
            return self.strategy.to_level_position(attempt)

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

        return self.strategy.to_level_position(attempt)

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
            self.strategy.to_level_position(Node(x, y))
            for x in range(self.minima.x, self.maxima.x)
            for y in range(self.minima.y, self.maxima.y)
            if node_check(x, y)
        )

    @_flattened
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
