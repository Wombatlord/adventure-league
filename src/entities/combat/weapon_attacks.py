from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generator

from src.entities.combat.attack_rules import AttackRules, RollOutcome
from src.entities.combat.damage import Damage
from src.entities.properties.meta_compendium import MetaCompendium
from src.world.node import Node

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.entity import Entity

Event = dict[str, Any]


class WeaponAttackMeta(type, metaclass=abc.ABCMeta):
    ap_cost: int = 0
    name: str = ""
    max_range: int = 0
    _fighter: Fighter
    weapon_type: str = ""

    def __new__(cls, *args, **kwargs):
        attack_class = super().__new__(cls, *args, **kwargs)
        MetaCompendium.all_attacks[attack_class.name] = attack_class
        return attack_class

    @abc.abstractmethod
    def attack(self, target) -> Event:
        raise NotImplementedError()

    @abc.abstractmethod
    def valid_target(self, target: Fighter | Node) -> bool:
        raise NotImplementedError()

    @property
    def fighter(self):
        return self._fighter

    @classmethod
    def live_check(cls, attacker, target):
        if attacker.owner.is_dead:
            raise ValueError(f"{attacker.owner.name=}: I'm dead jim.")

        if target.is_dead:
            raise ValueError(f"{target.name=}: He's dead jim.")


class NormalAttack(metaclass=WeaponAttackMeta):
    name: str = "Normal Attack"
    ap_cost: int = 1
    max_range: int = 1
    _fighter: Fighter

    def __init__(self, fighter) -> None:
        self._fighter = fighter

    @property
    def fighter(self):
        return self._fighter

    def attack(self, target: Entity) -> Generator[Event, None, None]:
        result = {}
        message = ""

        WeaponAttackMeta.live_check(self._fighter, target)
        # For choosing attack animation sprites
        self._fighter.in_combat = True
        target.fighter.in_combat = True

        yield from self.fighter.gear.weapon.emit_damage().resolve_damage(target)

        result.update({"attack": self._fighter.owner, "message": message})
        yield result

    def valid_target(self, target: Fighter | Node) -> bool:
        if not hasattr(target, "location"):
            return False

        if target.location is None:
            return False

        range = self._fighter.locatable.entities_in_range(
            room=self._fighter.encounter_context.get(),
            max_range=self._fighter.gear.weapon._range,
            entity_filter=lambda e: self._fighter.is_enemy_of(e.fighter),
        )

        can_see = target.owner in range and self._fighter.can_see(target)
        return can_see

    def aoe_at_node(self, node: Node | None = None) -> tuple[Node, ...] | None:
        if node is None:
            return tuple()
        if not isinstance(node, Node):
            raise TypeError(f"Expected a Node, got {node=}")

        return (node,)
