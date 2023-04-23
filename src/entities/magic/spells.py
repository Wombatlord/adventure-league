from __future__ import annotations

import abc
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.magic.caster import Caster

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

    def __init__(self, anchor: Node, shape: tuple[Node]):
        self.anchor = anchor
        self.shape = shape

    def get_shape(self) -> tuple[Node]:
        return self.shape


class Spell(metaclass=abc.ABCMeta):
    mp_cost: int = 0
    name: str = ""
    max_range: int = 0
    _caster: Caster
    effect_type: EffectType

    def __init__(self, caster: Caster):
        self._caster = caster
        self._target = None
        self.effect_type = None

    def cast(self, target: Fighter | Node) -> Generator[Event]:
        match self.effect_type:
            case EffectType.SELF:
                yield from self.self_cast()
            case EffectType.ENTITY:
                yield from self.entity_cast(target=target.owner)
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

    @abc.abstractmethod
    def valid_target(self, target: Node | Fighter) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def aoe_at_node(self, node: Node) -> AoETemplate | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def is_self_target(self) -> bool:
        raise NotImplementedError()


class MagicMissile(Spell):
    name: str = "magic missile"
    mp_cost: int = 1
    max_range: int = 1
    effect_type = EffectType.ENTITY

    def __init__(self, caster: Caster):
        super().__init__(caster=caster)
        self._damage: int = 1
        self._caster = caster

    def entity_cast(self, target: Fighter) -> Generator[Event, None, None]:
        target.hp -= self._damage
        return {
            "message": f"{self._caster.owner.owner.name} cast {self.name} at {target.owner.name}"
        }

    def valid_target(self, target: Fighter | Node) -> bool:
        if not isinstance(target, Fighter):
            return False

        if not target.is_enemy_of(self._caster.owner):
            return False

        return self._caster.owner.can_see(target)

    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return None

    def is_self_target(self) -> bool:
        return False


class Shield(Spell):
    name: str = "shield"
    mp_cost: int = 1
    max_range: int = 0
    effect_type = EffectType.SELF

    def __init__(self, caster: Caster):
        super().__init__(caster=caster)
        self._bonus_hp: int = 1
        self._caster = caster

    def self_cast(self) -> Generator[Event]:
        self._caster.owner.bonus_health += self._bonus_hp
        return {"message": f"{self._caster.owner.owner.name} shielded themselves."}

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


class Fireball(Spell):
    name: str = "fireball"
    mp_cost: int = 1
    max_range: int = 4
    effect_type = EffectType.AOE

    _n = Node(0, 0)
    template = (
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
        super().__init__(caster=caster)
        self._caster = caster
        self._damage: int = 1

    def aoe_cast(self, target: Node) -> Generator[Event]:
        template = self.aoe_at_node(target)
        room = self._caster.owner.encounter_context.get()

        yield {"message": f"{self._caster.owner.owner.name} cast {self.name}."}

        for entity in room.occupants:
            if entity.locatable.location in template:
                yield from entity.fighter.take_damage(self._damage)

    def valid_target(self, target: Fighter | Node):
        if not isinstance(target, Node):
            return False

        return self._caster.owner.can_see(target)

    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return AoETemplate(anchor=node, shape=self.template)

    def is_self_target(self) -> bool:
        return False


if TYPE_CHECKING:
    SpellFactory = Callable[[Caster], Spell]


basic_spell_book = [MagicMissile, Shield, Fireball]
