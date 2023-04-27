from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, Optional, Self

from src.entities.action.actions import (
    ActionCompendium,
    ActionMeta,
    ActionPoints,
    AttackAction,
    BaseAction,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.stats import FighterStats, HealthPool
from src.entities.entity import Entity
from src.entities.item.inventory import Consumable, Inventory
from src.entities.magic.caster import Caster, MagicAction
from src.world.node import Node
from src.world.ray import Ray

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

    def get(self) -> Room | None:
        return self.encounter_context

    def clear(self):
        self.encounter_context = None


# A class attached to any Entity that can fight
class Fighter:
    _readied_action: BaseAction | None
    _encounter_context: EncounterContext
    health: HealthPool

    def __init__(
        self,
        role: FighterArchetype,
        hp: int = 0,
        defence: int = 0,
        power: int = 0,
        level: int = 0,
        max_range: int = 0,
        speed: int = 0,
        caster: Caster = None,
        is_enemy: bool = False,
        is_boss: bool = False,
    ) -> None:
        if role is None:
            raise TypeError("The role cannot be None")
        self.owner: Optional[Entity] = None
        # -----Stats-----
        self.health = HealthPool(max=hp)
        self.stats = FighterStats(
            defence=defence, power=power, level=level, max_range=max_range, speed=speed
        )
        self.set_role(role)
        # -----State-----
        self.action_points = ActionPoints()
        self.caster = caster
        self.on_retreat_hooks = []
        self.is_enemy = is_enemy
        self.is_boss = is_boss
        self.retreating = False
        self._in_combat = False
        self._readied_action = None
        self._encounter_context = EncounterContext(self)

    def set_role(self, role: FighterArchetype):
        self.role = role
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
        defaults = [MoveAction, AttackAction, ConsumeItemAction, EndTurnAction]
        match self.role:
            case FighterArchetype.MELEE:
                optional = []

            case FighterArchetype.RANGED:
                optional = []

            case FighterArchetype.CASTER:
                optional = [MagicAction]

            case _:
                optional = []

        self.action_options = defaults + optional

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
        if action in self.action_options:
            return action.cost(self) <= self.action_points.current

        else:
            return False

    def request_action_choice(self):
        action_types = ActionCompendium.all_available_to(self)
        choices = {}
        for name, action_type in action_types.items():
            if not action_type == MagicAction:
                choices[name] = action_type.all_available_to(self)
            else:
                for spell in self.caster.spells:
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

    def take_damage(self, amount: int) -> Event:
        result = {}
        initial_hp = self.health.current

        self.health.decrease_current(amount)

        result.update(**self.owner.annotate_event({}))
        if self.health.current <= 0:
            self.health.current = 0
            self.owner.is_dead = True

            result.update(**{"dead": self})

        final_hp = self.health.current
        result.update(
            {
                "damage_taken": {
                    "recipient": self,
                    "hp_after": final_hp,
                    "amount": initial_hp - final_hp,
                },
            }
        )
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

    def can_see(self, target: Fighter | Node) -> bool:
        eye = self.location

        if isinstance(target, Fighter):
            target = target.location

        room = self.encounter_context.get()
        if not room:
            return False

        visible_nodes = Ray(eye).line_of_sight(room.space, target)

        return target in visible_nodes
