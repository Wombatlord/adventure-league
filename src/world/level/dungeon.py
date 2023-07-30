import random
from typing import Generator, Optional

from src.entities.entity import Entity
from src.entities.item.loot import Loot, Rewarder
from src.gui.biome_textures import BiomeName
from src.world.level.room import Room


class Dungeon(Rewarder):
    def __init__(
        self,
        max_enemies_per_room: int,
        min_enemies_per_room: int,
        rooms: list[Room],
        enemies: list[Entity],
        boss: Entity | None,
        description: Optional[str] = "NO DESC",
        treasure: Optional[int] = 0,
        xp_reward: Optional[int] = 0,
    ) -> None:
        self.biome = random.choice(BiomeName.all_biomes())
        self.current_room: Room | None = None
        self.rooms: list[Room] = rooms
        self.max_enemies_per_room = max_enemies_per_room
        self.min_enemies_per_room = min_enemies_per_room
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

    def claim_guild_xp(self) -> int:
        return self.loot.claim_guild_xp()

    def claim_gp(self) -> int:
        return self.loot.claim_gp()
