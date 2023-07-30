from __future__ import annotations

import abc
from enum import Enum
from random import randint
from typing import TYPE_CHECKING, Any, Generator

from src.entities.combat.damage import Damage
from src.entities.properties.meta_compendium import MetaCompendium

if TYPE_CHECKING:
    from src.entities.magic.caster import Caster
    from src.entities.combat.fighter import Fighter

from src.world.node import Node

Event = dict[str, Any]


class EffectType(Enum):
    SELF = "self"
    ENTITY = "entity"
    AOE = "aoe"


class AoE(metaclass=abc.ABCMeta):
    anchor: Node

    @abc.abstractmethod
    def get_shape(self) -> tuple[Node]:
        raise NotImplementedError()

    def __contains__(self, node: Node) -> bool:
        return any(node == n + self.anchor for n in self.get_shape())


class AoETemplate(AoE):
    anchor: Node
    shape: tuple[Node]

    def __init__(self, anchor: Node, shape: tuple[Node, ...]):
        self.anchor = anchor
        self.shape = shape

    def get_shape(self) -> tuple[Node]:
        return tuple(self.anchor + n for n in self.shape)


class SpellMeta(type, metaclass=abc.ABCMeta):
    def __new__(cls, *args, **kwargs):
        spell_class = super().__new__(cls, *args, **kwargs)
        MetaCompendium.all_spells[spell_class.name] = spell_class
        return spell_class

    @abc.abstractmethod
    def valid_target(self, target: Node | Fighter) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def aoe_at_node(self, node: Node) -> tuple[Node, ...] | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def is_self_target(self) -> bool:
        raise NotImplementedError()


class Spell:
    mp_cost: int = 0
    name: str = ""
    max_range: int = 0
    _caster: Caster
    effect_type: EffectType

    def cast(self, target: Fighter | Node) -> Generator[Event]:
        match self.effect_type:
            case EffectType.SELF:
                yield from self.self_cast()
            case EffectType.ENTITY:
                yield from self.entity_cast(target=target)
            case EffectType.AOE:
                yield from self.aoe_cast(target=target)

    def self_cast(self) -> Generator[Event]:
        raise NotImplementedError(
            f"Effect type is {self.effect_type}. This spell does not have a self_cast."
        )

    def entity_cast(self, target: Fighter) -> Generator[Event]:
        raise NotImplementedError(
            f"Effect type is {self.effect_type}. This spell does not have an entity_cast"
        )

    def aoe_cast(self, target: Node) -> Generator[Event]:
        raise NotImplementedError(
            f"Effect type is {self.effect_type}. This spell does not have an aoe_cast"
        )

    @property
    def caster(self):
        return self._caster


class MagicMissile(Spell, metaclass=SpellMeta):
    name: str = "Magic Missile"
    mp_cost: int = 1
    max_range: int = 1
    effect_type = EffectType.ENTITY

    def __init__(self, caster: Caster):
        self._damage: int = 5
        self._caster = caster

    def entity_cast(self, target: Fighter | None) -> Generator[Event, None, None]:
        if target is None:
            return

        yield {
            "message": f"{self._caster.owner.owner.name} cast {self.name} at {target.owner.name}"
        }
        yield {
            "message": f"{self.name} strikes {target.owner.name} for {self._damage}!"
        }
        yield target.take_damage(self._damage)

    def valid_target(self, target: Fighter | Node) -> bool:
        if not hasattr(target, "location"):
            return False

        if target.location is None:
            return False

        if not target.is_enemy_of(self._caster.owner):
            return False

        return self._caster.owner.can_see(target)

    def aoe_at_node(self, node: Node | None = None) -> tuple[Node, ...] | None:
        # return AoETemplate(anchor=node, shape=(Node(0, 0, 0),))
        if node is None:
            return tuple()
        if not isinstance(node, Node):
            raise TypeError(f"Expected a Node, got {node=}")

        return (node,)

    def is_self_target(self) -> bool:
        return False


class Shield(Spell, metaclass=SpellMeta):
    name: str = "Shield"
    mp_cost: int = 1
    max_range: int = 0
    effect_type = EffectType.SELF

    def __init__(self, caster: Caster):
        self._shield_value: int = 5
        self._caster = caster

    def self_cast(self) -> Generator[Event]:
        self._caster.owner.health.set_shield(self._shield_value)
        yield {"message": f"{self._caster.owner.owner.name} shielded themselves."}

    def valid_target(self, target: Fighter | Node) -> bool:
        if not isinstance(target, Fighter):
            return False

        if not target is self.caster.owner:
            return False

        return True

    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return None

    def is_self_target(self) -> bool:
        return True


class Fireball(Spell, metaclass=SpellMeta):
    name: str = "Fireball"
    mp_cost: int = 4
    max_range: int = 4
    effect_type = EffectType.AOE

    _n = Node(0, 0)
    template_shape = (
        _n.north.north,
        _n.north.east,
        _n.north,
        _n.north.west,
        _n.east.east,
        _n.east,
        _n,
        _n.west,
        _n.west.west,
        _n.south.east,
        _n.south,
        _n.south.west,
        _n.south.south,
    )

    def __init__(self, caster: Caster):
        self._caster = caster
        self._max_damage: int = 15
        self._min_damage: int = 5
        self._template = AoETemplate(anchor=Node(0, 0), shape=self.template_shape)

    def aoe_cast(self, target: Node) -> Generator[Event]:
        template = self.aoe_at_node(target)
        room = self._caster.owner.encounter_context.get()

        yield {"message": f"{self._caster.owner.owner.name} cast {self.name}."}

        for entity in room.occupants:
            if entity.locatable.location in template:
                damage_amount = randint(self._min_damage, self._max_damage)
                damage = Damage(
                    self.caster.owner, damage_amount, crit_chance=0, damage_type="magic"
                )
                yield {
                    "message": f"{self.name} scorches {entity.name} with a fireball!\n"
                }
                yield from damage.resolve_damage(entity)

    def valid_target(self, target: Fighter | Node):
        if hasattr(target, "location"):
            target = target.location
        if not isinstance(target, Node):
            return False

        can_see = self._caster.owner.can_see(target)
        return can_see

    def aoe_at_node(self, node: Node | None = None) -> tuple[Node, ...]:
        if node is None:
            return tuple()
        self._template.anchor = node
        return self._template.get_shape()

    def is_self_target(self) -> bool:
        return False
