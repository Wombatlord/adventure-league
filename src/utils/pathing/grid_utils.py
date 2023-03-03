from __future__ import annotations

from typing import Generator, NamedTuple

from astar import AStar


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
        x_within = self.minima.x <= item.x < self.maxima.x
        y_within = self.minima.y <= item.y < self.maxima.y

        return x_within and y_within and item not in self.exclusions

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if candidate in self:
                yield candidate

    def distance_between(self, n1: Node, n2: Node) -> int:
        return 1

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        return 1

    @property
    def height(self) -> int:
        return self.maxima.y - self.minima.y

    @property
    def width(self) -> int:
        return self.maxima.x - self.minima.x


class Node(NamedTuple):
    x: int
    y: int

    @property
    def east(self) -> Node:
        return Node(x=self.x + 1, y=self.y)

    @property
    def west(self) -> Node:
        return Node(x=self.x - 1, y=self.y)

    @property
    def north(self) -> Node:
        return Node(x=self.x, y=self.y + 1)

    @property
    def south(self) -> Node:
        return Node(x=self.x, y=self.y - 1)

    @property
    def adjacent(self) -> Generator[Node, None, None]:
        yield self.north
        yield self.east
        yield self.south
        yield self.west

    def __eq__(self, other: Node) -> bool:
        return self.x == other.x and self.y == other.y


def pretty_path(space: Space, start: Node, end: Node) -> str:
    row = [" "] * space.width
    empty = [[*row] for _ in range(space.height)]

    for exclusion in space.exclusions:
        empty[exclusion.y][exclusion.x] = "X"

    for place in path:
        empty[place.y][place.x] = "·"

    lines = map("".join, empty[::-1])

    return "\n".join(lines)
