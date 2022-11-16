from typing import Optional
from src.entities.entity import Entity


class Dungeon:
    def __init__(
        self,
        id: int,
        enemies: list[Entity],
        boss: Entity,
        description: Optional[str] = "NO DESC",
        treasure: Optional[str] = "NO TREASURE",
        xp_reward: Optional[int] = 0,
    ) -> None:
        self.id: int = id
        self.enemies: list[Entity] = enemies
        self.boss: Entity = boss
        self.description: Optional[str] = description
        self.treasure: Optional[str] = treasure
        self.xp_reward: Optional[int] = xp_reward

    def remove_corpses(self):
        # Iterate through enemies and remove dead enemies from the array.
        for i, enemy in enumerate(self.enemies):
            if enemy.is_dead:
                self.enemies.pop(i)
