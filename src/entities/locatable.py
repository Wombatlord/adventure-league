from __future__ import annotations

from enum import Enum
from random import choice
from typing import TYPE_CHECKING, Generator, Sequence

from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace

if TYPE_CHECKING:
    from src.entities.entity import Entity


class Orientation(Enum):
    NORTH = Node(0, 1)
    EAST = Node(1, 0)
    SOUTH = Node(0, -1)
    WEST = Node(-1, 0)


class Locatable:
    def __init__(
        self, owner: "Entity", location: Node, speed: int, space: PathingSpace
    ) -> None:
        self.owner = owner
        self.location = location
        self.space = space
        self.speed = speed
        self.orientation = Node(*choice([o.value for o in Orientation]))

    def path_to_target(self, target) -> tuple[Node, ...]:
        return self.space.get_path(self.location, target.location)

    def _no_move(self):
        return {
            "move": {
                "start": self.location,
                "end": self.location,
                "in_motion": False,
                "orientation": self.orientation,
            }
        }

    def approach_target(self, target: Locatable) -> Generator[dict]:
        yield {
            "message": f"{self.owner.name.name_and_title} moved toward {target.owner.name.name_and_title} with bad intentions"
        }
        if self.location == target.location:
            # attacker and target are overlapping.
            yield self.traverse(choice(self.adjacent_locations())),

        target_adjancencies = set(target.locatable.adjacent_locations())

        if self.location in target_adjancencies:
            # no traversal is necessary
            yield self._no_move()
            return

        # path ends in adjacent node to target
        path_to_target = self.path_to_target(target)
        dest_index = -1

        for i, place in enumerate(path_to_target):
            if place in target_adjancencies:
                dest_index = i
                break

        yield from self.traverse(path_to_target[: dest_index + 1])

    def traverse(self, path: Sequence[Node, ...]) -> Generator[dict]:
        if not path or len(path) == 1:
            yield self._no_move()
            return

        if self.speed < len(path):
            path = path[: self.speed + 1]

        start, *intermediate, destination = path
        to_traverse = [*intermediate, destination]

        for i, place in enumerate(to_traverse):
            prev = self.location
            action = self._step_action(prev, place == destination)
            self.location = place
            self.orientation = self.location - to_traverse[i - 1]
            yield action

    def _step_action(self, prev: Node, in_motion: bool) -> dict:
        return {
            "move": {
                "start": prev,
                "end": self.location,
                "in_motion": in_motion,
                "orientation": self.orientation,
            },
        }

    def reachable_places(self) -> tuple[Node, ...]:
        nodes = set()
        max_depth = self.speed
        def _recurse(start: Node, depth: int = 0):
            if depth >= max_depth or start in nodes:
                return
            for location in node.adjacent:
                if location in self.space:
                    nodes.add(location)
                    _recurse(location, depth=depth+1)




            

    def adjacent_locations(self) -> tuple[Node, ...]:
        """A getter for the tuple of nodes that are close enough to this Locatable for
        a range 0 interaction
        """
        # includes diagonals
        maximum_possile_adjacencies = (
            self.location.north,
            self.location.south,
            self.location.east,
            self.location.west,
            self.location.north.east,
            self.location.north.west,
            self.location.south.east,
            self.location.south.west,
        )

        return tuple(
            filter(
                # check the adjacent location is traversable
                lambda loc: loc in self.space,
                maximum_possile_adjacencies,
            )
        )
