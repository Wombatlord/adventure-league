from __future__ import annotations
from typing import Optional
from enum import Enum
from src.entities.entity import Entity

# Simple enum for providing formatted names with and without titles
class Title(Enum):
    ATK_WITH_TITLE = "attacker titled"
    ATK_WITHOUT_TITLE = "attacker without title"
    TAR_WITH_TITLE = "target titled"
    TAR_WITHOUT_TITLE = "target without title"

    def format_name(self, fighter: Fighter) -> str:
        match self:
            case Title.ATK_WITH_TITLE:
                return f"{fighter.owner.name.capitalize()} {fighter.owner.title}"
            
            case Title.ATK_WITHOUT_TITLE:
                return f"{fighter.owner.name.capitalize()}"

            case Title.TAR_WITH_TITLE:
                return f"{fighter.name.capitalize()} {fighter.title}"

            case Title.TAR_WITHOUT_TITLE:
                return f"{fighter.name.capitalize()}"

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

    def from_dict(self, dict) -> None:
        self.hp = dict.get('hp')
        self.defence = dict.get('defence')
        self.power = dict.get('power')
        self.level = dict.get('level')
        self.xp_reward = dict.get('xp_reward')
        self.current_xp = dict.get('current_xp')

    def take_damage(self, amount):
        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            self.owner.is_dead = True
            print(f"{self.owner.name.capitalize()} {self.owner.title} is dead!")

    def attack(self, target: Entity):
        if self.owner.is_dead or target.is_dead:
            return

        if target.is_dead:
            # raise ValueError(f"{self.owner.name}: he's dead jim.")
            return
        
        damage: int = self.power - target.fighter.defence

        atk_titled = Title.ATK_WITH_TITLE.format_name(self)
        atk_untitled = Title.ATK_WITHOUT_TITLE.format_name(self)
        tgt_titled = Title.TAR_WITH_TITLE.format_name(target)
        tgt_untitled = Title.TAR_WITHOUT_TITLE.format_name(target)

        if damage > 0:
            print(f"{atk_titled if self.owner.title else atk_untitled} hits {tgt_titled if target.title else tgt_untitled} for {damage}")
            
            target.fighter.take_damage(damage)
            
            print(f"{target.name.capitalize()} HP: " + str(target.fighter.hp) + "\n")

        else:
            print("no damage")
            return 0