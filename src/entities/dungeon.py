from typing import Optional, Generator
from src.entities.entity import Entity
from src.entities.loot import Loot, Rewarder

class Room:
    def __init__(self) -> None:
        self.enemies: list[Entity] = []
        self._cleared = False
        self.on_entry_hooks = []

    def add_entity(self, entity: Entity):
        self.enemies.append(entity)
        entity.on_death_hooks.append(self.remove)

    def remove(self, entity: Entity):
        if entity.fighter.is_enemy:
            self.enemies.pop(self.enemies.index(entity))

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
