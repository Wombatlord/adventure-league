from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Generator, Self

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity

Event = dict[str, Any]


class Damage:
    raw_damage: int = 0
    final_damage: int = 0
    target: Entity
    originator: Fighter

    def __init__(self, raw_damage, originator, target) -> None:
        self.originator = originator
        self.target = target
        self.raw_damage = raw_damage
        self.final_damage = 0

    @classmethod
    def calculate_raw(cls, attacker: Fighter, target: Entity) -> Self:
        atk_power = attacker.modifiable_stats.current.power
        target_def = target.fighter.modifiable_stats.current.defence

        raw_damage = 2 * int(atk_power**2 / (atk_power + target_def))

        return cls(int(raw_damage), attacker, target)

    def resolve_damage(self) -> Generator[Event, None, None]:
        result = {}

        # 10% chance to completely evade
        if random.randint(1, 10) == 1:
            self.final_damage = 0
            message = f"{self.target.name} evaded the attack!\n"
            result.update({"message": message})
            result.update({"damage": self.final_damage})

            yield result
            return

        # Resolve Damage if not evaded.
        yield from self.damage_confirm_message()
        yield from self._damage_reduction_by_defense()
        yield from self._final_resolved_damage()
        

    def damage_confirm_message(self) -> Event:
        originator_name = self.originator.owner.name
        weapon = self.originator.equipment.weapon
        target_name = self.target.name
        if weapon.attack_verb == "melee":
            yield {
                "message": f"{originator_name} hits {target_name} with their {originator_name}\n"
            }
        elif weapon.attack_verb == "ranged":
            yield {
                "message": f"{originator_name} shoots {target_name} with their {originator_name}\n"
            }

    def _damage_reduction_by_defense(self):
        # target.defence / 10 chance to reduce damage by 10%
        if random.randint(1, 10) < self.target.fighter.modifiable_stats.current.defence:
            reduction = 0.1
            self.final_damage = int(self.raw_damage - (self.raw_damage * reduction))
            message = f"{self.target.name}'s defence reduced the damage!\n"
        
        else:
            self.final_damage = self.raw_damage
            message = ""
        
        yield {"message": message}
    
    def _final_resolved_damage(self):
        result = {}
        message = f"{self.target.name} takes {self.final_damage} damage!\n"
        result.update({"message": message})

        if self.target.fighter.health.current - self.final_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            self.originator.in_combat = False

        damage_details = self.target.fighter.take_damage(self.final_damage)
        result.update(**damage_details)
        yield result
