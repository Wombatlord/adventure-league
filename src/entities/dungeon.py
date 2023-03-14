from typing import Generator, Optional

from src.entities.entity import Entity
from src.entities.loot import Loot, Rewarder
from src.utils.pathing.grid_utils import Node, Space


class Room:
    def __init__(self, size: tuple[int, int] = (10, 10)) -> None:
        self.enemies: list[Entity] = []
        self.occupants: list[Entity] = []
        self._cleared = False
        self.on_entry_hooks = []
        self.space = Space(Node(x=0, y=0), Node(*size), exclusions=set())
        self.entry_door = Node(x=0, y=5)

    def add_entity(self, entity: Entity):
        mob_spawns = self.mob_spawns_points()
        if entity.fighter.is_enemy:
            spawn_point = next(mob_spawns)
        else:
            spawn_point = self.entry_door

        entity.make_locatable(self.space, spawn_point=spawn_point)
        self.occupants.append(entity)
        if entity.fighter.is_enemy:
            self.enemies.append(entity)
        entity.on_death_hooks.append(self.remove)
        entity.on_death_hooks.append(Entity.flush_locatable)
        entity.fighter.on_retreat_hooks.append(lambda f: self.remove(f.owner))
        entity.fighter.on_retreat_hooks.append(
            lambda f: Entity.flush_locatable(f.owner)
        )

    def include_party(self, party: list[Entity]) -> None:
        for member in party:
            self.add_entity(member)

    def mob_spawns_points(self) -> Generator[Node, None, None]:
        left_wall = {Node(x=0, y=y) for y in self.space.y_range}
        while True:
            yield self.space.choose_random_node(
                excluding=left_wall,
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
        boss: Entity,
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

    def room_generator(self) -> Generator[None, None, Room]:
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
