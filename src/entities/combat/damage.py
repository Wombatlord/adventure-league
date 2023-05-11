from __future__ import annotations
import random
from typing import TYPE_CHECKING, Self


if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity


class Damage:
    raw_damage: int = 0
    final_damage: int = 0
    
    def __init__(self, raw_damage, originator) -> None:
        self.raw_damage = raw_damage
        self.originator = originator
        self.final_damage = 0
        
    @classmethod
    def calculate_raw(cls, attacker: Fighter) -> Self:
        actual_damage = attacker.modifiable_stats.current.power
        
        return cls(actual_damage, attacker)
    
    def apply_reductions(self, target: Entity):
        result = {}
        message = ""
        defence = target.fighter.modifiable_stats.current.defence
        
        actual_damage = 2 * int(self.raw_damage**2 / (self.raw_damage + defence))
        
        # 10% chance to completely evade
        if random.randint(1,10) == 1:
            self.final_damage = 0
            message += f"{target.name} evaded the attack!\n"
            result.update({"message": message})
            result.update({"damage": int(self.final_damage)})
            return result
        
        # target.defence / 10 chance to reduce damage by 10%
        if random.randint(1, 10) < target.fighter.modifiable_stats.current.defence:
            reduction = 0.1
            self.final_damage = actual_damage - (actual_damage * reduction)
            message += f"{target.name}'s defence reduced the damage!\n"
        
        result.update({"message": message})
        result.update({"damage": int(actual_damage)})
        
        if target.fighter.health.current - actual_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            self.originator.in_combat = False
        
        return result