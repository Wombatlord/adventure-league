from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Self

from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import FighterStats, StatAffix

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.entities.item.equippable import Equippable, EquippableConfig


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store(self, item: Equippable) -> None:
        ...


class Equipment:
    weapon: Equippable
    helmet: Equippable
    body: Equippable

    _equippable_slots = (
        "weapon",
        "helmet",
        "body",
    )

    __slots__ = (
        "owner",
        *_equippable_slots,
    )

    @classmethod
    def from_dict(cls, data: dict, owner: Fighter) -> Self | None:
        """Here we recreate the equipment of a Fighter.
        First we assign values to the __slots__ so that they exist.
        We use a closure to instantiate the equippable and prepare the affixes.
        Then assign the equippable to an equipment slot.
        We call equip_item outside this scope to warmup the caches.
        """
        instance = object.__new__(cls)

        instance.owner = owner
        instance.weapon = None
        instance.helmet = None
        instance.body = None

        def equips(owner):
            """
            Here we instantiate the equippable from the config dicts.
            As the config is all in dict forms, the affixes will initially be a dict rather than StatAffixes.
            Build an array of actual StatAffixes based on this config
            Then clear the affixes and _affixes arrays on both the equippable itself and the EquippableConfig
            Replace them with the affixes array containing actual StatAffixes build from those dict representations.
            """
            nonlocal slot
            affixes = []
            for afx in data[slot]["affixes"]:
                affixes.append(
                    StatAffix(
                        name=afx.get("name"),
                        modifier=Modifier(
                            FighterStats,
                            afx["modifier"]["percent"],
                            afx["modifier"]["percent"],
                        ),
                    )
                )

            ec = EquippableConfig(**data.get(slot).get("config"))
            equippable = Equippable(owner, config=ec)

            ec.affixes.clear()
            ec.affixes.extend(affixes)
            equippable._affixes.clear()
            equippable._affixes.extend(affixes)

            return equippable

        for slot in cls._equippable_slots:
            # if item := data.get(slot):
            #     ec = EquippableConfig(**item.get("config"))
            #     equippable = Equippable(owner, config=ec)

            #     instance.item = equippable

            # breakpoint()

            match data.get(slot).get("slot"):
                case "weapon":
                    instance.weapon = equips(instance)
                case "helmet":
                    instance.helmet = equips(instance)
                case "body":
                    instance.body = equips(instance)

        return instance

    def to_dict(self) -> dict:
        return {
            "weapon": self.weapon.to_dict() if self.weapon else None,
            "helmet": self.helmet.to_dict() if self.helmet else None,
            "body": self.body.to_dict() if self.body else None,
        }

    def __init__(self, owner: Fighter, weapon=None, helmet=None, body=None) -> None:
        self.owner = owner
        self.weapon = weapon
        self.helmet = helmet
        self.body = body

    def item_in_slot(self, slot) -> Equippable | None:
        if slot not in self._equippable_slots:
            return None
        return getattr(self, slot, None)

    def equip_item(self, item: Equippable, storage: Storage = None):
        slot = item.slot
        if slot not in self._equippable_slots:
            raise ValueError(f"Cannot equip item {item} in slot {slot}")

        self.unequip(slot, storage)
        item.on_equip(self.owner)
        setattr(self, slot, item)

    def unequip(self, slot: str, storage: Storage | None = None):
        if prev_item := self.item_in_slot(slot):
            prev_item.unequip()
            if storage is not None:
                storage.store(prev_item)
