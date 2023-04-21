from __future__ import annotations

import abc
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, NamedTuple

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.magic.caster import Caster
    
from src.world.node import Node

Event = dict[str, Any]

class EffectType(Enum):
    SELF = 0
    ENTITY = 1
    AOE = 2

class AoETemplate(NamedTuple):
    anchor: Node
    shape: tuple[Node]

class Spell(metaclass=abc.ABCMeta):
    mp_cost: int = 0
    name: str = ""
    max_range: int = 0
    _caster: Caster
    effect_type: EffectType
    
    def __init__(self, caster: Caster):
        self._caster = caster
        self._target = None

    @abc.abstractmethod
    def self_cast(self) -> Event:
        raise NotImplementedError()

    @abc.abstractmethod
    def entity_cast(self) -> Event:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def aoe_cast(self) -> Event:
        raise NotImplementedError()
    
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
    effect_value: int = 1
    max_range: int = 1
    effect_type = EffectType.ENTITY
    
    def __init__(self, caster: Caster):
        super().__init__(caster=caster)
        self._caster = caster
    
    def self_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use entity_cast method.")
    
    def entity_cast(self, target) -> Event:
        target.hp -= self.effect_value
        return {"message": f"{self._caster.owner.owner.name} cast {self.name} at {target.owner.name}"}
    
    def aoe_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use entity_cast method.")
    
    def valid_target(self, target: Fighter) -> bool:
        if target.is_enemy_of(self._caster.owner):
            return True
        else:
            return False

    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return None

    def is_self_target(self) -> bool:
        return False


class Shield(Spell):
    name: str = "shield"
    mp_cost: int = 1
    effect_value: int = 1
    max_range: int = 0
    effect_type = EffectType.SELF
    
    def __init__(self, caster: Caster):
        super().__init__(caster=caster)
        self._caster = caster

    def self_cast(self) -> Event:
        self._caster.owner.bonus_health += self.effect_value
        return {"message": f"{self._caster.owner.owner.name} shielded themselves."}
    
    def entity_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use self_cast method.")
    
    def aoe_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use self_cast method.")
    
    def valid_target(self, target: Fighter):
        if target is self.caster.owner:
            return True
        else:
            return False
    
    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:
        return None
    
    def is_self_target(self) -> bool:
        return True


class Fireball(Spell):
    name: str = "fireball"
    mp_cost: int = 1
    effect_value: int = 1
    max_range: int = 4
    effect_type = EffectType.AOE
    
    def __init__(self, caster: Caster):
        super().__init__(caster=caster)
        self._caster = caster

    def self_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use aoe_cast method.")
    
    def entity_cast(self) -> Event:
        raise NotImplementedError(f"Effect type is {self.effect_type}. Use aoe_cast method.")
    
    def aoe_cast(self, targets: list[Node]) -> Event:
        room = self._caster.owner.encounter_context
        for entity in room.encounter_context.occupants:
            if entity.fighter.location in targets:
                entity.fighter.hp = self.effect_value
                
        return {"message": f"{self._caster.owner.owner.name} cast {self.name}."}
    
    def valid_target(self, target: Node, valid_nodes: tuple[Node]):
        if target in valid_nodes:
            return True
        else:
            return False
    
    def aoe_at_node(self, node: Node | None = None) -> AoETemplate | None:            
        template = (*node.adjacent,)        
        return AoETemplate(anchor=node, shape=template)
    
    def is_self_target(self) -> bool:
        return False


SpellFactory = Callable[[Caster], Spell]

basic_spell_book = [MagicMissile, Shield, Fireball]