from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING, Callable, NamedTuple, Self
from src.entities.combat.archetypes import FighterArchetype

from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import (
    FighterStats,
    PercentPowerIncrease,
    RawDefenceIncrease,
    RawPowerIncrease,
    StatAffix,
)
from src.entities.combat.weapon_attacks import NormalAttack, WeaponAttackMeta
from src.entities.magic.spells import Fireball, MagicMissile, Shield, Spell
from src.entities.properties.meta_compendium import MetaCompendium

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
    def _prepare_attacks(self) -> list[WeaponAttackMeta]:
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
    _attacks: list[WeaponAttackMeta]
    _spells: list[Spell]
    _affixes: list[StatAffix]
    _available_attacks_cache: list[WeaponAttackMeta]
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
    def available_attacks(self) -> list[WeaponAttackMeta]:
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

    def _prepare_attacks(self) -> list[WeaponAttackMeta]:
        prepared = []
        for attack in self._attacks:
            if attack in MetaCompendium.all_registered_attacks():
                prepared.append(MetaCompendium.all_attacks[attack])

        return prepared

    def _prepare_spells(self) -> list[Spell]:
        prepared = []

        for spell in self._spells:
            if spell in MetaCompendium.all_registered_spells():
                prepared.append(MetaCompendium.all_spells[spell])

        return prepared

    @property
    def available_attacks(self) -> list[WeaponAttackMeta]:
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


def default_equippable_factory() -> Callable[[FighterArchetype], dict[str, Equippable]]:
    gearset_config = {
        "weapon": {"melee": (Sword,), "ranged": (Bow,), "caster": (SpellBook,)},
        "helmet": {"melee": (Helmet,), "ranged": (Helmet,), "caster": (Helmet,)},
        "body": {
            "melee": (Breastplate,),
            "ranged": (Breastplate,),
            "caster": (Breastplate,),
        },
    }

    def factory(role: FighterArchetype) -> dict[str, Equippable]:
        weapons = gearset_config.get("weapon", "")
        helmets = gearset_config.get("helmet", "")
        bodies = gearset_config.get("body", "")

        gear = {}
        def by_role(role):
            gear["weapon"] = Equippable(
                    owner=None, config=random.choice(weapons[role])
                )._init_affixes()
            gear["helmet"] = Equippable(
                owner=None, config=random.choice(helmets[role])
            )._init_affixes()
            gear["body"] = Equippable(
                owner=None, config=random.choice(bodies[role])
            )._init_affixes()
        
        match role:
            case role.MELEE:
                by_role(role.MELEE.value)

            case role.RANGED:
                by_role(role.RANGED.value)

            case role.CASTER:
                by_role(role.CASTER.value)
                
        return gear

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
