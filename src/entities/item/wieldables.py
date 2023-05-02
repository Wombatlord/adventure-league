from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Self

from src.entities.combat.attack_types import NormalAttack, WeaponAttack
from src.entities.item.equipment import Equippable
from src.entities.magic.spells import Fireball, MagicMissile, Shield, Spell

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class Wieldable(Equippable):
    _range: int
    _available_attacks: list[WeaponAttack] | None
    _available_spells: list[Spell] | None
    _attacks: list[WeaponAttack] | None
    _spells: list[Spell] | None
    _weapon_type: str
    _name: str
    _slot: str

    def __init__(
        self, owner: Fighter | None, item: WieldableConfig | None = None
    ) -> None:
        self._owner = owner
        self._slot = item.slot
        self._name = item.name
        self._range = item.range
        self._weapon_type = item.weapon_type
        self._attacks = item.attacks
        self._spells = item.spells
        self._available_attacks = None
        self._available_spells = None

    @property
    def slot(self) -> str:
        return self._slot
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def range(self) -> int:
        return self._range

    @property
    def available_attacks(self) -> list[WeaponAttack]:
        return self._available_attacks

    @property
    def available_spells(self) -> list[Spell]:
        return self._available_spells

    @property
    def weapon_type(self) -> str:
        return self._weapon_type

    def on_equip(self) -> Self:
        self._available_attacks = [
            attack(self._owner) for attack in self._prepare_attacks()
        ]
        self._available_spells = (
            [spell(self._owner.caster) for spell in self._prepare_spells()]
            if self._spells
            else None
        )
        return self

    def _prepare_attacks(self) -> list[WeaponAttack]:
        prepared = []
        for attack in self._attacks:
            match attack:
                case "NormalAttack":
                    prepared.append(NormalAttack)

        return prepared
    
    def _prepare_spells(self) -> list[Spell]:
        prepared = []
        for spell in self._spells:
            match spell:
                case "MagicMissile":
                    prepared.append(MagicMissile)
                case "Shield":
                    prepared.append(Shield)
                case "Fireball":
                    prepared.append(Fireball)

        return prepared

    def unequip(self):
        self._owner = None
        self._available_attacks = None
        self._available_spells = None


class WieldableConfig(NamedTuple):
    name: str = ""
    slot: str = ""
    weapon_type: str = ""
    range: int = 0
    attacks: list[str] | None = None
    spells: list[str] | None = None


class Sword(WieldableConfig):
    name = "sword"
    slot = "weapon"
    weapon_type = "melee"
    range = 1
    attacks = ["NormalAttack"]
    spells = None


class Bow(WieldableConfig):
    name = "bow"
    slot = "weapon"
    weapon_type = "ranged"
    range = 5
    attacks = ["NormalAttack"]
    spells = None


class SpellBook(WieldableConfig):
    name = "grimoire"
    slot = "weapon"
    weapon_type = "melee"
    range = 1
    attacks = ["NormalAttack"]
    spells = ["MagicMissile", "Shield", "Fireball"]
