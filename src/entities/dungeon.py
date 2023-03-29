from typing import Generator, Optional, Self

from src.entities.entity import Entity
from src.entities.loot import Loot, Rewarder
from src.world.level.room import basic_room
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class Room:
    def __init__(self, size: tuple[int, int] = (10, 10)) -> None:
        self.layout = None
        self.space = None
        self.set_layout(basic_room(size))
        self.enemies: list[Entity] = []
        self.occupants: list[Entity] = []
        self._cleared = False
        self.entry_door = Node(x=0, y=5) if size[1] > 5 else Node(0, 0)

    def set_layout(self, layout: tuple[Node, ...]) -> Self:
        self.layout = layout
        self.space = PathingSpace.from_level_geometry(self.layout)
        return self

    def update_pathing_obstacles(self):
        """
        Used to synchronise the traversable locations with updated entity locations
        Returns:

        """
        exclusions = {occupant.locatable.location for occupant in self.occupants}
        self.space.exclusions = exclusions

    def add_entity(self, entity: Entity):
        mob_spawns = self.mob_spawns_points()
        if entity.fighter.is_enemy:
            spawn_point = next(mob_spawns)
        else:
            spawn_point = self.space.choose_next_unoccupied(self.entry_door)

        entity.make_locatable(self.space, spawn_point=spawn_point)
        self.occupants.append(entity)  # <- IMPORTANT:
        self.update_pathing_obstacles()  # <- don't change the order of these two!

        if entity.fighter.is_enemy:
            self.enemies.append(entity)

        entity.on_death_hooks.extend(
            [
                self.remove,
                Entity.flush_locatable,
            ]
        )
        entity.fighter.on_retreat_hooks.extend(
            [
                lambda f: self.remove(f.owner),
                lambda f: Entity.flush_locatable(f.owner),
            ]
        )

    def include_party(self, party: list[Entity]) -> None:
        for member in party:
            self.add_entity(member)

    def mob_spawns_points(self) -> Generator[Node, None, None]:
        while True:
            yield self.space.choose_random_node(
                excluding=self.space.exclusions,
            )

    def remove(self, entity: Entity):
        if hasattr(entity, "owner"):
            entity = entity.owner
        elif not isinstance(entity, Entity):
            raise TypeError(
                f"Can only remove Entities and owned components from the room, got {entity}",
            )
        if entity.fighter.is_enemy:
            self.enemies.pop(self.enemies.index(entity))
        self.occupants.pop(self.occupants.index(entity))

    @property
    def cleared(self):
        return self._cleared

    @cleared.setter
    def cleared(self, new_value):
        current_value = self.cleared

        if new_value != current_value:
            print("ROOM CLEAR!")


class Dungeon(Rewarder):
    def __init__(
        self,
        max_enemies_per_room: int,
        rooms: list[Room],
        enemies: list[Entity],
        boss: Entity | None,
        description: Optional[str] = "NO DESC",
        treasure: Optional[int] = 0,
        xp_reward: Optional[int] = 0,
    ) -> None:
        self.current_room: Room = Room()
        self.rooms: list[Room] = rooms
        self.max_enemies_per_room = max_enemies_per_room
        self.enemies: list[Entity] = enemies
        self.boss: Entity = boss
        self.description: Optional[str] = description
        self.treasure: Optional[int] = treasure
        self.xp_reward: Optional[int] = xp_reward
        self.loot = Loot(xp=self.xp_reward, gp=self.treasure)
        self.cleared = False

    def move_to_next_room(self):
        self.current_room = next(self.room_generator())

    def room_generator(self) -> Generator[Room, None, None]:
        for room in self.rooms:
            yield room

    def remove_corpses(self):
        # Iterate through enemies and remove dead enemies from the array.
        for i, enemy in enumerate(self.enemies):
            if enemy.is_dead:
                self.enemies.pop(i)

    def peek_reward(self) -> str:
        return str(self.loot)

    def claim_xp(self) -> int:
        return self.loot.claim_xp()

    def claim_gp(self) -> int:
        return self.loot.claim_gp()
