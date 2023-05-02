from __future__ import annotations
import abc

from typing import TYPE_CHECKING, Self

from src.entities.combat.attack_types import WeaponAttack
from src.entities.magic.spells import Spell

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.item.wieldables import Wieldable


class Equipment:
    weapon: Wieldable
    __slots__ = ("owner", "weapon", "helmet", "body")

    def __init__(self, owner: Fighter, weapon=None, helmet=None, body=None) -> None:
        self.owner = owner
        self.weapon = weapon
        self.helmet = helmet
        self.body = body

    def can_equip(self, item: Equippable) -> bool:
        if not isinstance(item, Equippable):
            return False

        match item.slot:
            case "weapon":
                if self.weapon is None:
                    return True
            case "helmet":
                if self.helmet is None:
                    return True
            case "body":
                if self.body is None:
                    return True

        return False

    def equip_item(self, item: Equippable):
        if self.can_equip(item):
            match item.slot:
                case "weapon":
                    self.weapon = item
                case "helmet":
                    self.helmet = item
                case "body":
                    self.body = item

    def unequip_item(self, item, storage):
        match item.slot:
            case "weapon":
                self.weapon = None
            case "helmet":
                self.helmet = None
            case "body":
                self.body = None

        item.unequip()
        storage.move_to(item)


class Equippable(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_equip(self) -> Self:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def unequip(self):
        raise NotImplementedError()
    
    @abc.abstractmethod
    def _prepare_attacks(self) -> list[WeaponAttack]:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def _prepare_spells(self) -> list[Spell]:
        raise NotImplementedError()
