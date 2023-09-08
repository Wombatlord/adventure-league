from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Generator

from src.engine.events_enum import EventTopic

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity

Event = dict[str, Any]


class Damage:
    raw_damage: int = 0
    final_damage: int = 0
    originator: Fighter

    def __init__(
        self, originator, raw_damage, crit_chance, damage_type="physical"
    ) -> None:
        self.originator = originator
        self.damage_type = damage_type
        self.raw_damage = raw_damage
        self.crit_chance = crit_chance
        self.final_damage = 0

    def resolve_damage(self, target: Entity) -> Generator[Event, None, None]:
        yield from self._attack_message(target)
        result = {}

        # evasion % chance to completely evade
        if (
            random.randint(0, 100)
            <= target.fighter.gear.modifiable_equipped_stats.current.evasion * 100
        ) and self.damage_type == "physical":
            self.final_damage = 0
            message = f"{target.name} evaded the attack!\n"
            result.update({EventTopic.MESSAGE: message})

            yield result
            return

        # Resolve Damage if not evaded.
        yield from self._critical_confirm()
        yield from self._damage_reduction_by_defense(target)
        yield from self._final_resolved_damage(target)

    def _attack_message(self, target) -> Event:
        if self.damage_type == "magic":
            # Spells implement their own attack messages
            return
        originator_name = self.originator.owner.name
        weapon = self.originator.gear.weapon
        target_name = target.name
        if weapon.attack_verb == "melee":
            yield {
                EventTopic.MESSAGE: f"{originator_name} swings at {target_name} with their {weapon.name}\n"
            }
        elif weapon.attack_verb == "ranged":
            yield {
                EventTopic.MESSAGE: f"{originator_name} shoots at {target_name} with their {weapon.name}\n"
            }

    def _critical_confirm(self):
        message = ""
        if random.randint(1, 100) <= self.crit_chance:
            self.raw_damage *= 2
            yield {EventTopic.MESSAGE: "CRITICAL!"}

        else:
            yield {EventTopic.MESSAGE: message}

    def _damage_reduction_by_defense(
        self, target: Entity
    ) -> Generator[Event, None, None]:
        mitigation = self._mitigation(
            max_mitigation=0.4,
            damage_fallthrough=0.8,
            defence=target.fighter.modifiable_stats.current.defence,
        )
        self.final_damage = (1 - mitigation) * self.raw_damage
        mitigation_percent = f"{mitigation * 100:.2f}"
        message = (
            f"{target.name}'s defence reduced the damage by {mitigation_percent}%!\n"
        )

        yield {EventTopic.MESSAGE: message}

    def _final_resolved_damage(self, target: Entity):
        result = {}
        damage = int(self.final_damage)
        message = f"{target.name} takes {damage} damage!\n"
        result.update({EventTopic.MESSAGE: message})

        if target.fighter.health.current - self.final_damage <= 0:
            # If the attack will kill, we will no longer be "in combat" until the next attack.
            self.originator.in_combat = False

        damage_details = target.fighter.take_damage(damage)
        if damage_details.get("emit_exp", None):
            dungeon = self.originator.encounter_context.get().dungeon
            dungeon.loot._team_xp_to_be_awarded.append(damage_details["emit_exp"])

        result.update(**damage_details)
        yield result

    def _mitigation(
        self, max_mitigation: float, damage_fallthrough: float, defence: int
    ) -> float:
        return max_mitigation * (1 - damage_fallthrough**defence)
