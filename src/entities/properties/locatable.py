from __future__ import annotations

from enum import Enum
from random import choice
from typing import TYPE_CHECKING, Callable, Generator, Sequence

from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity
    from src.world.level.room import Room


Path = tuple[Node]


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

    def path_to_target(self, target: Locatable | Fighter) -> tuple[Node, ...]:
        return self.path_to_destination(target.location)

    def path_to_destination(self, destination: Node) -> tuple[Node, ...]:
        return self.space.get_path(self.location, destination)

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

    def traverse(self, path: Sequence[Node]) -> Generator[dict]:
        if not path or len(path) == 1:
            yield self._no_move()
            return

        if self.speed < len(path):
            path = path[: self.speed + 1]

        start, *intermediate, destination = path
        to_traverse = [*intermediate, destination]

        for i, place in enumerate(to_traverse):
            prev = self.location
            event = self._step_event(prev, place, place != destination)
            self.location = place
            self.orientation = self.location - to_traverse[i - 1]
            yield event

    def _step_event(self, before: Node, after: Node, in_motion: bool) -> dict:
        return {
            "move": {
                "start": before,
                "end": after,
                "in_motion": in_motion,
                "orientation": self.orientation,
            },
        }

    def available_moves(self, speed: int | None = None) -> tuple[tuple[Node, ...], ...]:
        paths = []
        for node in self.space.all_included_nodes():
            path = self.path_to_destination(node)
            if path is None or len(path) <= 1:
                continue
            if len(path) > speed + 1:
                continue

            paths.append(path)

        return tuple(paths)

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

    def entities_in_range(
        self,
        room: Room,
        max_range: int,
        entity_filter: Callable[[Entity], bool] = lambda e: True,
    ) -> list[Entity]:
        """
        This function can be used to retrieve a list of all locatable entities in range of
        an entity's current position
        Args:
            room: Room. The space shared by the entities
            max_range:  The range within which an entity should be considered in range
            entity_filter: A function that can be applied to each entity to filter. It should
            return True if the entity should be included in the resulting list. This will
            only be applied to entities that are actually in range

        Returns:

        """
        in_range = []
        for occupant in room.occupants:
            if (
                # do this before calculating the path length to avoid unnecessary
                # calculation of paths for entities that we can't or shouldn't check
                not occupant.locatable
                or occupant.locatable is self
                or not entity_filter(occupant)
            ):
                continue

            path = self.path_to_target(occupant.locatable)
            if path is None:
                print(f"{occupant.name} {occupant.locatable.location=} is unreachable")
                continue
            path_length = len(path)
            is_in_range = path_length - (max_range + 1) <= 0

            if is_in_range:
                in_range.append(occupant)

        return in_range

    def nearest_entity(
        self, room: Room, entity_filter: Callable[[Entity], bool] = lambda e: True
    ) -> Entity | None:
        shortest_path = None
        closest_entity = None
        for occupant in room.occupants:
            # Ignore self, and apply the filter to rule out occupants based on the
            # provided filter predicate
            if occupant is self.owner or not entity_filter(occupant):
                continue

            path = self.path_to_target(occupant.locatable)
            # if there is no path to the target, go to the next
            if path is None:
                continue

            # if no shortest path has been set, then the current one is by default
            # the shortest
            if shortest_path is None:
                shortest_path = path
                closest_entity = occupant
                continue

            # A length 2 path is a single step, so can't be closer than this without
            # occupying the same node
            if len(shortest_path) <= 2:
                break

            # if the path is shorter than the shortest yet, then record the current
            # as the new shortest and set the closest entity
            if len(shortest_path) > len(path):
                shortest_path = path
                closest_entity = occupant

        return (closest_entity, shortest_path)
