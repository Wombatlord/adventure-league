from __future__ import annotations

from random import randint
from typing import Any, Optional

from src.entities.entity import Entity
from src.utils.pathing.grid_utils import Node

Action = dict[str, Any]


# A class attached to any Entity that can fight
class Fighter:
    def __init__(
        self,
        is_enemy: bool,
        hp: int = 0,
        defence: int = 0,
        power: int = 0,
        level: int = 0,
        xp_reward: int = 0,
        current_xp: int = 0,
        speed: int = 0,
        is_boss: bool = False,
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
        self.on_retreat_hooks = []
        self.is_enemy = is_enemy
        self.is_boss = is_boss
        self.target = None
        self.speed = speed
        self._in_combat = False

    def get_dict(self) -> dict:
        d = self.__dict__
        result = {}
        desired_items = {"retreating", "hp", "is_enemy"}

        for k, v in d.items():
            if k in desired_items:
                result[k] = v

        return result

    def from_dict(self, dict) -> None:
        self.hp = dict.get("hp")
        self.defence = dict.get("defence")
        self.power = dict.get("power")
        self.level = dict.get("level")
        self.xp_reward = dict.get("xp_reward")
        self.current_xp = dict.get("current_xp")

    def request_target(self, targets: list[Fighter]) -> Action:
        return {
            "message": f"{self.owner.name.name_and_title} readies their attack! Choose a target!",
            "await_input": self,
            "target_selection": {
                "paths": [
                    self.owner.locatable.path_to_target(t.owner.locatable)
                    for t in targets
                ],
                "targets": targets,
                "confirmation_callback": None,
            },
        }

    def choose_target(self, targets) -> int:
        possible = len(targets) - 1

        return randint(0, possible)

    @property
    def in_combat(self):
        return self._in_combat

    @in_combat.setter
    def set_in_combat(self, state: bool):
        self._in_combat = state

    @property
    def location(self) -> Node | None:
        if self.is_locatable:
            return self.owner.locatable.location

    @property
    def locatable(self):
        if self.is_locatable():
            return self.owner.locatable

    def is_locatable(self):
        return self.owner.locatable is not None

    def choose_nearest_target(self, targets: list[Fighter]) -> int:
        if len(targets) < 1:
            raise ValueError("Supply at least one potential target")

        if self.owner.locatable is None:
            raise TypeError(
                f"The attacker is not locateable: {self.owner.name.name_and_title=}"
            )

        closest = None
        # bigger than any dungeon room, so the first checked target will always be closer
        min_distance = 100000

        for target_idx, possible_target in enumerate(targets):
            if possible_target.owner.locatable is None:
                raise TypeError(
                    f"The target is not locateable: {possible_target.owner.name.name_and_title=}"
                )

            distance = self.owner.locatable.space.get_path_len(
                self.owner.locatable.location,
                possible_target.owner.locatable.location,
            )
            if distance is None:
                continue

            # is the possible target the closest so far?
            if distance < min_distance:
                min_distance = distance
                closest = target_idx

            # We can attack already
            if min_distance <= 1:
                break

        if closest is None:
            raise ValueError(
                f"The fighter {self.owner.name.name_and_title} could not traverse to any of the potential targets"
            )

        return closest

    @property
    def incapacitated(self) -> bool:
        is_incapacitated = self.owner.is_dead or self.retreating
        return is_incapacitated

    def initial_health(self) -> Action:
        result = {}
        result.update(**self.owner.annotate_event({}))
        return result

    def take_damage(self, amount) -> Action:
        result = {}
        self.hp -= amount
        result.update(**self.owner.annotate_event({}))
        if self.hp <= 0:
            self.hp = 0
            self.owner.is_dead = True

            result.update(**{"dead": self})

        return result

    def attack(self, target: Entity) -> Action:
        result = {}
        if self.owner.is_dead:
            raise ValueError(f"{self.owner.name=}: I'm dead jim.")

        if target.is_dead:
            raise ValueError(f"{target.name=}: He's dead jim.")

        my_name = self.owner.name.name_and_title

        target_name = target.name.name_and_title

        succesful_hit: int = self.power - target.fighter.defence
        result.update(**{"attack": self.owner})

        if not self.in_combat:
            self.set_in_combat = True

        if not target.fighter.in_combat:
            target.fighter.set_in_combat = True

        if succesful_hit > 0:
            actual_damage = int(
                2 * self.power**2 / (self.power + target.fighter.defence)
            )

            result.update(
                **{"message": f"{my_name} hits {target_name} for {actual_damage}\n"}
            )

            if target.fighter.hp - actual_damage <= 0:
                # If the attack will kill, we will no longer be "in combat" until the next attack.
                self.set_in_combat = False

            result.update(**target.fighter.take_damage(actual_damage))

        else:
            result.update(**{"message": f"{my_name} fails to hit {target_name}!"})

            if not self.is_enemy:
                self.commence_retreat()

        return result

    def commence_retreat(self):
        self.retreating = True
        hooks = self.on_retreat_hooks
        while hooks and (hook := hooks.pop(0)):
            hook(self)

    def clear_hooks(self):
        self.on_retreat_hooks = []
