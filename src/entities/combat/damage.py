from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity

Event = dict[str, Any]


class Damage:
    raw_damage: int = 0
    final_damage: int = 0
    originator: Fighter

    def __init__(self, raw_damage, originator) -> None:
        self.originator = originator
        self.raw_damage = raw_damage
        self.final_damage = 0

    def resolve_damage(self, target: Entity) -> Generator[Event, None, None]:
        yield from self._attack_message(target)
        result = {}

        # evasion % chance to completely evade
        if (
            random.randint(0, 100)
            <= target.fighter.equipment.base_equipped_stats.evasion * 100
        ):
            self.final_damage = 0
            message = f"{target.name} evaded the attack!\n"
            result.update({"message": message})

            yield result
            return

        # Resolve Damage if not evaded.
        yield from self._critical_confirm(target)
        yield from self._damage_reduction_by_defense(target)
        yield from self._final_resolved_damage(target)

    def _attack_message(self, target) -> Event:
        originator_name = self.originator.owner.name
        weapon = self.originator.equipment.weapon
        target_name = target.name
        if weapon.attack_verb == "melee":
            yield {
                "message": f"{originator_name} swings at {target_name} with their {weapon.name}\n"
            }
        elif weapon.attack_verb == "ranged":
            yield {
                "message": f"{originator_name} shoots at {target_name} with their {weapon.name}\n"
            }

    def _critical_confirm(self, target):
        message = ""
        if (
            random.randint(0, 100)
            <= target.fighter.equipment.modifiable_equipped_stats.current.crit
        ):
            self.raw_damage *= 2
            yield {"message": "CRITICAL!"}

        else:
            yield {"message": message}

    def _damage_reduction_by_defense(
        self, target: Entity
    ) -> Generator[Event, None, None]:
        mitigation = self._exponential_decay(
            0.4, 0.9, target.fighter.modifiable_stats.current.defence
        )
        self.final_damage = self.raw_damage - (self.raw_damage * mitigation)
        mitigation_percent = "{:.2f}".format(mitigation * 100)
        message = (
            f"{target.name}'s defence reduced the damage by {mitigation_percent}%!\n"
        )

        yield {"message": message}

    def _final_resolved_damage(self, target):
        result = {}
        damage = int(self.final_damage)
        message = f"{target.name} takes {damage} damage!\n"
        result.update({"message": message})

        if target.fighter.health.current - self.final_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            self.originator.in_combat = False

        damage_details = target.fighter.take_damage(damage)
        result.update(**damage_details)
        yield result

    def _exponential_decay(self, limit: float, decay: float, stat: int) -> float:
        return limit * (1 - decay**stat)
