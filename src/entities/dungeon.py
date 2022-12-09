from typing import Optional
from src.entities.entity import Entity
from src.entities.loot import Loot, Rewarder

class Dungeon(Rewarder):
    def __init__(
        self,
        id: int,
        enemies: list[Entity],
        boss: Entity,
        description: Optional[str] = "NO DESC",
        treasure: Optional[int] = 0,
        xp_reward: Optional[int] = 0,
    ) -> None:
        self.id: int = id
        self.enemies: list[Entity] = enemies
        self.boss: Entity = boss
        self.description: Optional[str] = description
        self.treasure: Optional[int] = treasure
        self.xp_reward: Optional[int] = xp_reward
        self.loot = Loot(xp=self.xp_reward, gp=self.treasure)

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
