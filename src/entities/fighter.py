from __future__ import annotations
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
        self.retreating = False

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

    def from_dict(self, dict) -> None:
        self.hp = dict.get("hp")
        self.defence = dict.get("defence")
        self.power = dict.get("power")
        self.level = dict.get("level")
        self.xp_reward = dict.get("xp_reward")
        self.current_xp = dict.get("current_xp")

    def take_damage(self, amount):
        results = []

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            self.owner.is_dead = True
            results.append(
                {"message": f"{self.owner.name.name_and_title()} is dead!"}
            )
            # print(f"{self.owner.name.name_and_title()} is dead!")
        
        return results

    def attack(self, target: Entity):
        results = []
        if self.owner.is_dead or target.is_dead:
            raise ValueError(f"{self.owner.name}: he's dead jim.")

        my_name = self.owner.name.name_and_title()

        target_name = target.name.name_and_title()

        succesful_hit: int = self.power - target.fighter.defence

        if succesful_hit > 0:
            actual_damage = int(
                2 * self.power**2 / (self.power + target.fighter.defence)
            )

            results.append(
                {
                    "message": f"{my_name} hits {target_name} for {actual_damage}\n"
                }
            )

            # print(f"{my_name} hits {target_name} for {actual_damage}\n")
            result = target.fighter.take_damage(actual_damage)
            results.extend(result)
            
            return results
        
        else:
            results.append(
                {
                    "message": f"{my_name} fails to hit {target_name}!"
                }
            )

            results.append(
                {
                    "message": f"{my_name} retreats!"
                }
            )

            self.retreating = True
            return results
