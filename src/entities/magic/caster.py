from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.entities.magic.spells import Spell

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.entities.magic.spells import Spell

Event = dict[str, Any]


class MpPool:
    def to_dict(self):
        return {
            "max": self.max,
            "current": self.current
        }
    
    def __init__(self, max):
        self._max = max
        self._current = max

    def spend(self, amount: int):
        self._current -= amount

    def can_cast(self, spell: Spell) -> bool:
        return self.can_spend(spell.mp_cost)

    def can_spend(self, amount: int) -> bool:
        return self._current >= amount

    def recharge(self, amount: int | None = None):
        """
        Supply an amount to recharge by that amount (capped at max mp).
        Default behaviour is recharge to max.
        """
        if amount is None:
            self._current = self._max

        else:
            self._current = min(self._max, self._current + amount)

    @property
    def current(self) -> int:
        return self._current

    @property
    def max(self) -> int:
        return self._max

class Caster:
    def to_dict(self):
        return {"mp_pool": self.mp_pool.to_dict()}
    
    def __init__(self, max_mp: int):
        self.owner: Fighter | None = None
        self.mp_pool = MpPool(max=max_mp)

    def set_owner(self, owner: Caster) -> Caster:
        self.owner = owner
        return self

    @property
    def current_mp(self) -> int:
        return self.mp_pool.current
