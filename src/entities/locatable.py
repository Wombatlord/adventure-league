from __future__ import annotations

from random import choice
from typing import TYPE_CHECKING

from src.utils.pathing.grid_utils import Node, Space
from enum import Enum

if TYPE_CHECKING:
    from src.entities.entity import Entity

class Orientation(Enum):
    NORTH = Node(0, 1)
    EAST = Node(1, 0)
    SOUTH = Node(0, -1)
    WEST = Node(-1, 0)

class Locatable:
    def __init__(
        self, owner: "Entity", location: Node, speed: int, space: Space
    ) -> None:
        self.owner = owner
        self.location = location
        self.space = space
        self.speed = speed
        self.orientation = choice([*Orientation])

    def approach_target(self, target: Locatable) -> dict | None:
        msg_fragment = {
            "message": f"{self.owner.name.name_and_title} moved toward {target.owner.name.name_and_title} with bad intentions"
        }
        if self.location == target.location:
            # attacker and target are overlapping.
            return {
                **self.traverse_toward(choice(self.adjacent_locations())),
                **msg_fragment,
            }

        path_to_target = self.space.get_path(self.location, target.location)
        target_adjancencies = set(target.locatable.adjacent_locations())

        first_place = path_to_target[0]
        if first_place in target_adjancencies:
            # no traversal is necessary
            return {
                "move": {
                    "start": self.location,
                    "end": self.location,
                    "in_motion": False,
                    "orientation": self.orientation,
                }
            }

        for place in path_to_target:
            if place in target_adjancencies:
                return {
                    **self.traverse_toward(place),
                    **msg_fragment,
                }

    def traverse_toward(self, destination: Node) -> dict:
        start = Node(*self.location)
        path = self.space.get_path(self.location, destination)

        if len(path) <= self.speed:
            # If speed would go beyond the end of the path, move to the end of the path.
            self.location = path[-1]
            self.orientation = self.location - path[-2]
            return

        # Otherwise, move as far as along the path as speed allows.
        self.location = path[self.speed]
        self.orientation = self.location - path[self.speed-1]

        return {
            "move": {
                "start": start,
                "end": self.location,
                "in_motion": self.location != destination,
                "orientation": self.orientation,
            },
        }

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
