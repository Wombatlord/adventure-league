from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING, Any, Generator, Optional, Self

from src.entities.action.actions import (
    ActionCompendium,
    ActionMeta,
    ActionPoints,
    BaseAction,
)
from src.entities.entity import Entity
from src.entities.item.inventory import Consumable, Inventory
from src.world.node import Node

if TYPE_CHECKING:
    from src.world.level.room import Room

Event = dict[str, Any]


class EncounterContext:
    def __init__(self, fighter: Fighter):
        self.encounter_context = None
        self.fighter = fighter

    def set(self, room: Room):
        self.encounter_context = room
        self.fighter.on_retreat_hooks.append(lambda f: f.encounter_context.clear())
        self.fighter.owner.on_death_hooks.append(
            lambda e: e.fighter.encounter_context.clear()
        )

    def get(self) -> Room:
        return self.encounter_context

    def clear(self):
        self.encounter_context = None


# A class attached to any Entity that can fight
class Fighter:
    _readied_action: BaseAction | None
    _encounter_context: EncounterContext

    def __init__(
        self,
        role: str,
        hp: int = 0,
        defence: int = 0,
        power: int = 0,
        level: int = 0,
        max_range: int = 0,
        speed: int = 0,
        current_xp: int = 0,
        is_enemy: bool = False,
        is_boss: bool = False,
    ) -> None:
        self.owner: Optional[Entity] = None
        # -----Stats-----
        self.role = role
        self.max_hp = hp
        self.hp = hp
        self.defence = defence
        self.power = power
        self.level = level
        self.max_range = max_range
        self.speed = speed
        self.current_xp = current_xp
        self.action_points = ActionPoints()
        # -----State-----
        self.action_options = None
        self.on_retreat_hooks = []
        self.is_enemy = is_enemy
        self.is_boss = is_boss
        self.retreating = False
        self._target = None
        self._prev_target = None
        self._in_combat = False
        self._current_item = None
        self._forfeit_turn = False
        self._readied_action = None
        self._encounter_context = EncounterContext(self)
        self.set_action_options()

    def set_owner(self, owner: Entity) -> Self:
        self.owner = owner
        if not self.owner.inventory:
            self.owner.inventory = Inventory(owner=owner, capacity=1)
        return self

    @property
    def encounter_context(self) -> EncounterContext:
        return self._encounter_context

    def is_enemy_of(self, other: Fighter) -> bool:
        return self.is_enemy is not other.is_enemy

    def get_dict(self) -> dict:
        d = self.__dict__
        result = {}
        desired_items = {"retreating", "hp", "is_enemy", "defence", "power"}

        for k, v in d.items():
            if k in desired_items:
                result[k] = v

        return result

    def set_action_options(self):
        print(self.role)
        match self.role:
            case "melee":
                self.action_options = ["move", "attack", "use item", "end turn"]

            case "ranged":
                self.action_options = ["move", "ranged attack", "use item", "end turn"]

            case _:
                self.action_options = ["end turn"]

    def ready_action(self, action: BaseAction) -> bool:
        self._readied_action = action
        return True

    def is_ready_to_act(self) -> bool:
        return self._readied_action is not None

    def can_act(self) -> bool:
        return self.action_points.current > 0

    def act(self) -> Generator[Event]:
        action = self._readied_action()
        self._readied_action = None
        yield from action

    def does(self, action: ActionMeta) -> bool:
        if action.name in self.action_options:
            return action.cost(self) <= self.action_points.current

        else:
            return False

    def request_action_choice(self):
        action_types = ActionCompendium.all_available_to(self)
        choices = {}
        for name, action_type in action_types.items():
            choices[name] = action_type.all_available_to(self)

        event = {}
        if not self.is_enemy:
            event[
                "message"
            ] = f"{self.owner.name.name_and_title} requires your input milord"

        yield {
            **event,
            "await_input": self,
            "choices": choices,
        }

    def on_turn_start(self) -> Generator[Event]:
        self.action_points.on_turn_start()
        self._forfeit_turn = False
        yield {"turn_start": self}

    def on_turn_end(self) -> Generator[Event]:
        yield {"turn_end": self}

    @property
    def in_combat(self):
        return self._in_combat

    @in_combat.setter
    def in_combat(self, state: bool):
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

    @property
    def incapacitated(self) -> bool:
        is_incapacitated = self.owner.is_dead or self.retreating
        return is_incapacitated

    def take_damage(self, amount) -> Event:
        result = {}
        self.hp -= amount
        result.update(**self.owner.annotate_event({}))
        if self.hp <= 0:
            self.hp = 0
            self.owner.is_dead = True

            result.update(**{"dead": self})

        return result

    def consume_item(self, item: Consumable) -> Generator[Event, None, None]:
        yield item.consume(self.owner.inventory)

    def commence_retreat(self):
        self.retreating = True
        hooks = self.on_retreat_hooks
        while hooks and (hook := hooks.pop(0)):
            hook(self)

    def clear_hooks(self):
        self.on_retreat_hooks = []
