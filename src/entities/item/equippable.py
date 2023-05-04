from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Self

from src.entities.combat.attack_types import NormalAttack, WeaponAttack
from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import (
    FighterStats,
    PercentPowerIncrease,
    RawDefenceIncrease,
    RawPowerIncrease,
    StatAffix,
)
from src.entities.magic.spells import Fireball, MagicMissile, Shield, Spell

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class Equippable:
    _slot: str
    _name: str
    _range: int
    _attack_verb: str
    _attacks: list[WeaponAttack]
    _spells: list[Spell]
    _affixes: list[StatAffix]
    _available_attacks_cache: list[WeaponAttack]
    _available_spells_cache: list[Spell]

    def __init__(
        self, owner: Fighter | None, item: EquippableConfig | None = None
    ) -> None:
        self._owner = owner
        self._config = item
        self._slot = item.slot
        self._name = item.name
        self._range = item.range
        self._attack_verb = item.attack_verb
        self._attacks = item.attacks
        self._spells = item.spells
        self._affixes = item.affixes
        self._available_attacks_cache = []
        self._available_spells_cache = []

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
        return self._available_attacks_cache

    @property
    def available_spells(self) -> list[Spell]:
        return self._available_spells_cache

    @property
    def attack_verb(self) -> str:
        return self._attack_verb

    def _atk_cache_warmup(self):
        self._available_attacks_cache = (
            [attack(self._owner) for attack in self._prepare_attacks()]
            if self._attacks
            else []
        )

    def _spell_cache_warmup(self):
        self._available_spells_cache = (
            [spell(self._owner.caster) for spell in self._prepare_spells()]
            if self._spells
            else []
        )

    def on_equip(self) -> Self:
        self._owner.modifiable_stats.set_modifiers(self.modifiers())
        self._atk_cache_warmup()
        self._spell_cache_warmup()

        return self

    def _prepare_attacks(self) -> list[WeaponAttack]:
        prepared = []
        for attack in self._attacks:
            match attack:
                case NormalAttack.name:
                    prepared.append(NormalAttack)

        return prepared

    def _prepare_spells(self) -> list[Spell]:
        prepared = []
        for spell in self._spells:
            match spell:
                case MagicMissile.name:
                    prepared.append(MagicMissile)
                case Shield.name:
                    prepared.append(Shield)
                case Fireball.name:
                    prepared.append(Fireball)

        return prepared

    @property
    def available_attacks(self) -> list[WeaponAttack]:
        if not self._available_attacks_cache:
            self._atk_cache_warmup()
        return self._available_attacks_cache

    @property
    def available_spells(self) -> list[Spell]:
        if not self._available_spells_cache:
            self._spell_cache_warmup()
        return self._available_spells_cache

    def unequip(self):
        self._owner = None
        self._available_attacks_cache = None
        self._available_spells_cache = None

    def modifiers(self) -> list[Modifier[FighterStats]]:
        return [affix.modifier() for affix in self._affixes]


class EquippableConfig(NamedTuple):
    name: str = ""
    slot: str = ""
    attack_verb: str = ""
    range: int = 0
    attacks: list[str] | None = None
    spells: list[str] | None = None
    affixes: list = []


# Example Configs
Helmet = EquippableConfig(name="helmet", slot="helmet", affixes=[PercentPowerIncrease])

Breastplate = EquippableConfig(
    name="breastplate",
    slot="body",
    affixes=[RawPowerIncrease, RawDefenceIncrease],
)

Sword = EquippableConfig(
    name="sword",
    slot="weapon",
    attack_verb="melee",
    range=1,
    attacks=[NormalAttack.name],
    spells=[],
    affixes=[RawPowerIncrease],
)

Bow = EquippableConfig(
    name="bow",
    slot="weapon",
    attack_verb="ranged",
    range=5,
    attacks=[NormalAttack.name],
    spells=[],
)

SpellBook = EquippableConfig(
    name="grimoire",
    slot="weapon",
    attack_verb="melee",
    range=1,
    attacks=[NormalAttack.name],
    spells=[MagicMissile.name, Shield.name, Fireball.name],
)
