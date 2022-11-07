from typing import Optional
from src.entities.entity import Entity

# A class attached to any Entity that can fight
class Fighter:
    def __init__(
        self,
        hp: int = 0,
        defence: int = 0,
        power: int = 0,
        level: int = 0,
        xp_reward: int = 0,
        current_xp: int = 0,
    ) -> None:
        self.owner: Optional[Entity] = None
        self.max_hp = hp
        self.hp = hp
        self.defence = defence
        self.power = power
        self.level = level
        self.xp_reward = xp_reward
        self.current_xp = current_xp

    def get_dict(self) -> dict:
        result = {
            "max_hp": self.max_hp,
            "hp": self.hp,
            "defence": self.defence,
            "power": self.power,
            "level": self.level,
            "xp_reward": self.xp_reward,
            "current_xp": self.current_xp,
        }

        return result
