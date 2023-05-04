from __future__ import annotations
import abc
from typing import TYPE_CHECKING, Callable, NamedTuple, Self

from src.entities.combat.attack_types import NormalAttack, WeaponAttack
from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import (
    FighterStats,
    PercentPowerIncrease,
    RawDefenceIncrease,
    RawPowerIncrease,
    StatAffix,
)
from src.entities.magic.spells import Fireball, MagicMissile, Shield, Spell, SpellCompendium

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class EquippableABC(metaclass=abc.ABCMeta):
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

    @abc.abstractmethod
    def modifiers(self) -> list[Modifier[FighterStats]]:
        raise NotImplementedError()


class Equippable(EquippableABC):
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
        self, owner: Fighter | None, config: EquippableConfig | None = None
    ) -> None:
        self._owner = owner
        self._config = config
        self._slot = config.slot
        self._name = config.name
        self._range = config.range
        self._attack_verb = config.attack_verb
        self._attacks = config.attacks
        self._spells = config.spells
        self._affixes = config.affixes
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

    def on_equip(self, owner) -> Self:
        self._owner = owner
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
            if spell in SpellCompendium.all_available_to():
                prepared.append(SpellCompendium.all_spells[spell])

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
        return [affix for affix in self._affixes]

    def _init_affixes(self) -> Self:
        self._affixes = [affix.modifier() for affix in self._affixes]

        return self

    @classmethod
    def init_affixes(cls, owner: Fighter | None, config: EquippableConfig):
        return cls(owner, config)._init_affixes()


def equippable_factory(config: EquippableConfig) -> Callable[[None], Equippable]:
    def factory():
        return Equippable(owner=None, config=config)._init_affixes()

    return factory


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
