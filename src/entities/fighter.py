from __future__ import annotations

import functools
from typing import Any, Generator, Optional, Self

from src.entities.entity import Entity
from src.entities.inventory import Consumable, Inventory, InventoryItem, Throwable
from src.world.node import Node

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
        self._target = None
        self._prev_target = None
        self.speed = speed
        self._in_combat = False
        self._current_item = None
        self._forfeit_turn = False
        self._current_destination = None

    def set_owner(self, owner: Entity) -> Self:
        self.owner = owner
        if not self.owner.inventory:
            self.owner.inventory = Inventory(owner=owner, capacity=1)
        return self

    def get_dict(self) -> dict:
        d = self.__dict__
        result = {}
        desired_items = {"retreating", "hp", "is_enemy", "defence", "power"}

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
        paths = [
            *filter(
                lambda p: p is not None,
                [
                    self.owner.locatable.path_to_target(t.owner.locatable)
                    for t in targets
                ],
            )
        ]

        if not paths:
            self._forfeit_turn = True
            yield {
                "forfeit": self,
                "message": f"{self.owner.name} is biding their time until a target is reachable",
            }
            return

        def _on_confirm(idx) -> bool:
            if not self._current_item:
                self.provide_item(Consumable())
            return self.provide_target(targets[idx])

        yield {
            "message": f"{self.owner.name.name_and_title} readies their attack! Choose a target using the up and down keys.",
            "await_input": self,
            "target_selection": {
                "paths": [
                    self.owner.locatable.path_to_target(t.owner.locatable)
                    for t in targets
                ],
                "targets": targets,
                "on_confirm": _on_confirm,
                "default": targets.index(self.last_target())
                if self.last_target()
                else 0,
            },
        }

    def on_turn_start(self):
        self._forfeit_turn = False

    def choose_item(self):
        self._current_item = Consumable()
        return {}

    def request_item_use(self):
        return {
            "message": f"Use an item from {self.owner.name.name_and_title}'s inventory?",
            "await_input": self,
            "item_selection": {
                "inventory_contents": self.owner.inventory.items,
                "on_confirm": lambda item_idx: self.provide_item(
                    self.owner.inventory.items[item_idx]
                ),
                "default_item": self.owner.inventory.items[0],
            },
        }

    def request_move_instruction(self):
        def _on_confirm(self, destination: node) -> bool:
            self.provide_destination(destination)
            return True

        return {
            "message": f"Choose a move for {self.owner.name.name_and_title}",
            "":
            "move_selection": {
                "default_location": self.location,
                "on_confirm": _on_confirm,
            }
        }

    def provide_destination(self, destination: Node):
        self._current_destination = destination 

    def provide_item(self, item: InventoryItem):
        self._current_item = item
        return True

    def current_target(self) -> Fighter | None:
        self._cleanse_targets()
        return self._target

    def last_target(self) -> Fighter | None:
        self._cleanse_targets()
        return self._prev_target

    def provide_target(self, target: Fighter | None) -> bool:
        if self._target is not None:
            self._prev_target = self._target
        self._target = target
        self._cleanse_targets()
        return True

    def _cleanse_targets(self):
        if self._prev_target and self._prev_target.incapacitated:
            self._prev_target = None
        if self._target and self._target.incapacitated:
            self._target = None

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

        self.provide_target(targets[closest])

        return {"target_chosen": self.current_target()}

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

    def attack(self, target: Entity | None = None) -> Action:
        if target is not None:
            self.provide_target(target.fighter)

        target = self.current_target().owner

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

        self._prev_target = target.fighter
        self.provide_target(None)

        return result

    def consume_item(self) -> Generator[Action, None, None]:
        item: Consumable = self._current_item or Consumable()
        self._current_item = None
        yield item.consume(self.owner.inventory)

    def chosen_consumable(self) -> Consumable:
        return self._current_item or Consumable()

    def throw_item(self, item: Throwable):
        if item in self.owner.inventory:
            return item.throw(self.owner.inventory)

    def commence_retreat(self):
        self.retreating = True
        hooks = self.on_retreat_hooks
        while hooks and (hook := hooks.pop(0)):
            hook(self)

    def clear_hooks(self):
        self.on_retreat_hooks = []

    def turn_is_forfeit(self) -> bool:
        return self._forfeit_turn
