from __future__ import annotations

import abc
from typing import Callable, Generator, Iterable, Protocol

from src.world.node import Node


class Space(Protocol):
    def __contains__(self, node: Node) -> bool:
        pass

    @property
    @abc.abstractmethod
    def x_range(self) -> Iterable[int]:
        pass

    @property
    @abc.abstractmethod
    def y_range(self) -> Iterable[int]:
        pass


class PathingStrategy(abc.ABC):
    @abc.abstractmethod
    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        pass

    @abc.abstractmethod
    def distance_between(self, n1: Node, n2: Node) -> int:
        pass

    @abc.abstractmethod
    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int | float:
        pass

    @abc.abstractmethod
    def to_level_position(self, n: Node) -> Node:
        pass


class HeightMapStrategy(PathingStrategy):
    space: Space
    max_step_height: float
    height_map: Callable[[Node], float]

    def __init__(
        self, space: Space, max_step_height: float, height_map: Callable[[Node], float]
    ):
        self.space = space
        self.max_step_height = max_step_height
        self.height_map = height_map

    def _step_height(self, from_node: Node, to_neighbour: Node) -> float:
        return self.height_map(to_neighbour) - self.height_map(from_node)

    def _can_traverse(self, from_node: Node, to_neighbour: Node) -> bool:
        return abs(self._step_height(from_node, to_neighbour)) <= abs(
            self.max_step_height
        )

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if candidate in self.space and self._can_traverse(
                from_node=node, to_neighbour=candidate
            ):
                yield candidate

    def distance_between(self, n1: Node, n2: Node) -> int:
        return 1 if sum(abs(delta) for delta in (n1 - n2)[:2]) == 1 else 1.5

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int | float:
        return n1.distance_to(n2)

    def to_level_position(self, n: Node) -> Node:
        level_pos = Node(*n[:2], z=self.height_map(n))
        return level_pos


class DefaultStrategy(PathingStrategy):
    space: Space

    def __init__(self, space: Space):
        self.space = space

    def neighbors(self, node: Node) -> Generator[Node, None, None]:
        for candidate in node.adjacent:
            if candidate in self.space:
                yield candidate

    def distance_between(self, n1: Node, n2: Node) -> int:
        return 1 if sum(abs(delta) for delta in (n1 - n2)) == 1 else 1.5

    def heuristic_cost_estimate(self, n1: Node, n2: Node) -> int:
        return 1

    def to_level_position(self, n: Node) -> Node:
        return n
