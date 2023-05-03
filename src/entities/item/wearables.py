from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Self

from src.entities.combat.stats import (
    PercentPowerIncrease,
    RawDefenceIncrease,
    RawPowerIncrease,
    StatAffix,
)
from src.entities.item.equipment import Equippable

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class Wearable(Equippable):
    _name: str

    def __init__(self, owner: Fighter, item: WearableConfig) -> None:
        self._owner = owner
        self._config = item
        self._slot = item.slot
        self._name = item.name
        self._affixes = item.affixes

    @property
    def slot(self):
        return self._slot

    @property
    def name(self):
        return self._name

    @property
    def affixes(self):
        return self._affixes

    def on_equip(self) -> Self:
        self._owner.stats.modifiers.extend(self.affixes)
        return self

    def on_unequip(self) -> Self:
        self._owner.stats.modifiers.pop(self.affixes)


class WearableConfig(NamedTuple):
    name: str = ""
    slot: str = ""
    affixes: list[tuple[StatAffix, int]] = []


Helmet = WearableConfig(
    name="helmet", slot="helmet", affixes=[(PercentPowerIncrease, 10)]
)

Breastplate = WearableConfig(
    name="breastplate",
    slot="body",
    affixes=[(RawPowerIncrease, 2), (RawDefenceIncrease, 2)],
)
