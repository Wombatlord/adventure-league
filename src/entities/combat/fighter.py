from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, Optional, Self

import yaml

from src.entities.action.actions import (
    ActionMeta,
    ActionPoints,
    BaseAction,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.action.magic_action import MagicAction
from src.entities.action.weapon_action import WeaponAttackAction
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.modifiable_stats import ModifiableStats
from src.entities.combat.stats import FighterStats, HealthPool
from src.entities.item.equipment import Equipment
from src.entities.item.inventory import Consumable, Inventory
from src.entities.magic.caster import Caster
from src.entities.properties.meta_compendium import MetaCompendium
from src.entities.sprites import EntitySprite
from src.world.node import Node
from src.world.ray import Ray

if TYPE_CHECKING:
    from src.world.level.room import Room
    from src.entities.entity import Entity

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
    modifiable_stats: ModifiableStats
    _caster: Caster | None

    @classmethod
    def from_dict(cls, data: dict | None, owner: Entity) -> Self | None:
        if data is None:
            return None
        instance = object.__new__(cls)
        instance.owner = owner
        instance.__dict__ = {
            **data,
            "health": HealthPool.from_dict(data.get("health")),
            "stats": FighterStats(**data.get("stats")),
            "action_points": ActionPoints.from_dict(data.get("action_points")),
            "equipment": Equipment.from_dict(data.get("equipment"), owner=instance),
            "encounter_context": EncounterContext(fighter=instance),
        }

        if data.get("caster") is not None:
            instance.__dict__["caster"] = Caster.from_dict(
                data.get("caster"), owner=instance
            )

        
        instance.set_role(data.get("role"))
        instance.modifiable_stats = ModifiableStats(
            FighterStats, base_stats=instance.stats
        )
        

        return instance

    def to_dict(self) -> dict:
        return {
            "role": self.role.name,
            "health": self.health.to_dict(),
            "stats": self.stats._asdict(),
            "action_points": self.action_points.to_dict(),
            "equipment": self.equipment.to_dict(),
            "caster": self.caster.to_dict() if self.caster else None,
        }

    def __init__(
        self,
        role: FighterArchetype,
        hp: int = 0,
        defence: int = 0,
        power: int = 0,
        level: int = 0,
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
            defence=defence, power=power, level=level, speed=speed
        )
        self.modifiable_stats = ModifiableStats(FighterStats, base_stats=self.stats)
        self.equipment = Equipment(owner=self)
        self.set_role(role)
        # -----State-----
        self.action_points = ActionPoints()
        self._caster = None
        self.caster = caster
        self.on_retreat_hooks = []
        self.is_enemy = is_enemy
        self.is_boss = is_boss
        self.retreating = False
        self._in_combat = False
        self._readied_action = None
        self._encounter_context = EncounterContext(self)

    @classmethod
    def from_yaml(cls, loader: yaml.Loader, node=None) -> Self:
        f_gen: Generator[Fighter, None, None] = loader.construct_yaml_object(node, cls)
        f = next(f_gen)
        try:
            next(f_gen)
        except StopIteration:
            pass

        breakpoint()
        from src.entities.combat.fighter_factory import select_textures

        sprite_config = select_textures(f.owner.species, f)

        f.owner.set_entity_sprite(
            EntitySprite(
                idle_textures=sprite_config.idle_textures,
                attack_textures=sprite_config.attack_textures,
            )
        )
        return f

    @property
    def caster(self) -> Caster | None:
        return self._caster

    @caster.setter
    def caster(self, value: Caster | None):
        self._caster = value
        if value is not None:
            self._caster.set_owner(self)

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
        defaults = [WeaponAttackAction, MoveAction, ConsumeItemAction, EndTurnAction]
        match self.role:
            case FighterArchetype.MELEE | "MELEE":
                optional = []

            case FighterArchetype.RANGED | "RANGED":
                optional = []

            case FighterArchetype.CASTER | "CASTER":
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
            match action.name:
                case WeaponAttackAction.name:
                    return action.cost(self) <= self.action_points.current
                case _:
                    return action.cost(self) <= self.action_points.current

        else:
            return False

    def request_action_choice(self):
        action_types = MetaCompendium.all_actions_available_to(self)
        choices = {}
        for name, action_type in action_types.items():
            if action_type == WeaponAttackAction:
                for atk in self.equipment.weapon.available_attacks:
                    choices[name] = action_type.all_available_to(self)

            elif not action_type == MagicAction:
                choices[name] = action_type.all_available_to(self)

            else:
                for spell in self.equipment.weapon.available_spells:
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
        if isinstance(target, Fighter):
            target = target.location

        eye = self.location
        if target == eye:
            return False

        room = self.encounter_context.get()
        if not room:
            return False

        visible_nodes = Ray(eye).line_of_sight(room.space, target)

        return target in visible_nodes

    def line_of_sight_to(self, node: Node) -> tuple[Node]:
        room = self.encounter_context.get()
        if not room:
            return tuple()

        visible_nodes = Ray(self.location).line_of_sight(room.space, node)
        return tuple(visible_nodes[: visible_nodes.index(node) + 1])
