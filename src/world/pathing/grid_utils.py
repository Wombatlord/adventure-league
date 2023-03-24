from __future__ import annotations

import random
from functools import lru_cache
from random import randint
from typing import Callable, Generator, Iterable, NamedTuple

from astar import AStar

_ROOT_TWO = 2**0.5


class Space(AStar):
    minima: Node
    maxima: Node
    exclusions: set[Node]

    def __init__(self, minima: Node, maxima: Node, exclusions: set[Node] | None = None):
        if exclusions is None:
            exclusions = set()

        self.minima = minima
        self.maxima = maxima
        self.exclusions = exclusions

    def __contains__(self, item: Node) -> bool:
        return self.in_bounds(item) and item not in self.exclusions

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

    @lru_cache(maxsize=2)
    def get_path(self, start: Node, finish: Node) -> tuple[Node, ...] | None:
        # we exclude all occupied nodes so any paths from occupied nodes (i.e. all combat pathfinding)
        # will need to have the start/end node added back to the pathing space temporarily
        deferred_restore = [
            end if end not in self else False for end in (start, finish)
        ]
        for include in deferred_restore:
            include and self._include(include)

        path = self.astar(start, finish)

        # after we've got the path, we make sure that if it wasn't in the space before we started
        # then it won't be after we return
        for exclude in deferred_restore:
            exclude and self._exclude(exclude)

        if path is None:
            return

        return tuple(path)

    def _include(self, node: Node) -> None:
        self.exclusions -= {node}  # idempotent remove from set

    def _exclude(self, node: Node) -> None:
        self.exclusions |= {node}  # idempotent add to set

    def get_path_len(self, start: Node, end: Node) -> int | None:
        path = self.get_path(start, end)

        if path is None:
            return

        return len([*path])

    def choose_random_node(self, excluding: set[Node] = ()) -> Node:
        # if there are extra exclusions create a temp space with those exclusions as well as the pre-existing exclusions
        tmp_space = self
        if excluding:
            tmp_space = Space(
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
        breakpoint()
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


class Node(NamedTuple):
    x: int
    y: int
    z: int = 0

    @property
    def east(self) -> Node:
        return Node(x=self.x + 1, y=self.y, z=self.z)

    @property
    def west(self) -> Node:
        return Node(x=self.x - 1, y=self.y, z=self.z)

    @property
    def north(self) -> Node:
        return Node(x=self.x, y=self.y + 1, z=self.z)

    @property
    def south(self) -> Node:
        return Node(x=self.x, y=self.y - 1, z=self.z)

    @property
    def up(self) -> Node:
        return Node(x=self.x, y=self.y, z=self.z + 1)

    @property
    def down(self) -> Node:
        return Node(x=self.x, y=self.y, z=self.z - 1)

    @property
    def adjacent(self, include_diag=True, three_d=False) -> Generator[Node, None, None]:
        no_move = lambda n: n
        traversals_ns = (
            lambda n: n.north,
            no_move,
            lambda n: n.south,
        )
        traversals_ew = (
            lambda n: n.east,
            no_move,
            lambda n: n.west,
        )
        traversals_ud = (
            (
                lambda n: n.up,
                no_move,
                lambda n: n.down,
            )
            if three_d
            else (no_move,)
        )  # just stay in the plane if not 3d

        if not include_diag:
            # just move one node in + and - in each direction (east-west, north-south, up-down if relevant)
            yield from (
                move(self)
                for move in traversals_ud + traversals_ns + traversals_ew
                if move != no_move
            )
        else:
            # create the full set of 3x3 above and below plus the in-plane movements
            yield from (
                ns_move(ew_move(ud_move(self)))
                for ns_move in traversals_ns  # north and south traversals
                for ew_move in traversals_ew  # east and west traversals
                for ud_move in traversals_ud  # this includes above and below if three_d
                if (ns_move, ew_move, ud_move)
                != (no_move, no_move, no_move)  # exclude self from adjacent
            )

    def __eq__(self, other: Node) -> bool:
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __sub__(self, other: Node) -> Node:
        return Node(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other: Node) -> Node:
        return Node(self.x + other.x, self.y + other.y, self.z + other.z)


def pretty_path(space: Space, start: Node, end: Node) -> str:
    row = [" "] * space.width
    empty = [[*row] for _ in range(space.height)]

    for exclusion in space.exclusions:
        empty[exclusion.y][exclusion.x] = "X"

    for place in space.astar(start, end):
        empty[place.y][place.x] = "·"

    lines = map("".join, empty[::-1])

    return "\n".join(lines)
