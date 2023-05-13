from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING, Callable, NamedTuple, Self

from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.damage import Damage
from src.entities.combat.modifiable_stats import ModifiableStats, Modifier
from src.entities.combat.stats import (
    EquippableStats,
    FighterStats,
    PercentCritIncrease,
    PercentPowerIncrease,
    RawDefenceIncrease,
    RawPowerIncrease,
    StatAffix,
)
from src.entities.combat.weapon_attacks import NormalAttack, WeaponAttackMeta
from src.entities.magic.spells import Fireball, MagicMissile, Shield, Spell, SpellMeta
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
    def fighter_modifiers(self) -> list[Modifier[FighterStats]]:
        raise NotImplementedError()


class Equippable(EquippableABC):
    _slot: str
    _name: str
    _range: int
    _attack_verb: str
    _attacks: list[str]
    _spells: list[str]
    _fighter_affixes: list[StatAffix]
    _equipment_affixes: list[StatAffix]
    _available_attacks_cache: list[WeaponAttackMeta]
    _available_spells_cache: list[Spell]
    _modifiable_stats: ModifiableStats

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
        self._fighter_affixes = config.fighter_affixes
        self._equipment_affixes = config.equipment_affixes
        self._stats = config.stats
        self._modifiable_stats = ModifiableStats(EquippableStats, self._stats)
        self._available_attacks_cache = []
        self._available_spells_cache = []
        self._init_affixes()
        
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
    def stats(self) -> ModifiableStats:
        return self._modifiable_stats.current

    @property
    def available_attacks(self) -> list[WeaponAttackMeta]:
        return self._available_attacks_cache

    @property
    def available_spells(self) -> list[Spell]:
        return self._available_spells_cache

    @property
    def attack_verb(self) -> str:
        return self._attack_verb

    def dice(self, die_count: int, faces: int) -> int:
        roll = 0
        for _ in range(die_count):
            roll += random.randint(1, faces)
        return roll

    def emit_damage(self) -> Damage:
        dies = int(self.stats.attack_dice)
        faces = self.stats.attack_dice_faces
        roll_base_damage = self.dice(dies, faces)
        max_damage = self._owner.modifiable_stats.current.power + roll_base_damage

        return Damage(max_damage, self._owner)

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

    def on_equip(self, owner: Fighter) -> Self:
        self._owner = owner
        self._owner.modifiable_stats.set_modifiers(self.fighter_modifiers())
        self._atk_cache_warmup()
        self._spell_cache_warmup()

        return self

    def _prepare_attacks(self) -> list[WeaponAttackMeta]:
        prepared = []
        for attack in self._attacks:
            if attack in MetaCompendium.all_registered_attacks():
                prepared.append(MetaCompendium.all_attacks[attack])

        return prepared

    def _prepare_spells(self) -> list[SpellMeta]:
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

    def _init_affixes(self):
        """
        This is called on instantiation of a new equippable,
        It rolls fresh affixes which replace the lambda waiting to be invoked.
        """
        self._init_fighter_affixes()     
        self._init_equipment_affixes()

    def _init_equipment_affixes(self):
        mods = []
        for affix in self._equipment_affixes:
            mods.append(affix())
        self._equipment_affixes = mods

    def _init_fighter_affixes(self):
        mods = []
        for affix in self._fighter_affixes:
            mods.append(affix())
        self._fighter_affixes = mods
        
    def fighter_modifiers(self) -> list[Modifier[FighterStats]]:
        return [affix.modifier for affix in self._fighter_affixes]

    def equipment_modifiers(self) -> list[Modifier[EquippableStats]]:
        return [affix.modifier for affix in self._equipment_affixes]


def default_equippable_factory(
    gearset_config: dict | None = None,
) -> Callable[[FighterArchetype], dict[str, Equippable]]:
    gearset_config = gearset_config or {
        "_weapon": {"melee": (Sword,), "ranged": (Bow,), "caster": (SpellBook,)},
        "_helmet": {"melee": (Helmet,), "ranged": (Helmet,), "caster": (Helmet,)},
        "_body": {
            "melee": (Breastplate,),
            "ranged": (Breastplate,),
            "caster": (Breastplate,),
        },
    }

    def factory(role: FighterArchetype) -> dict[str, Equippable]:
        weapons = gearset_config.get("_weapon", {})
        helmets = gearset_config.get("_helmet", {})
        bodies = gearset_config.get("_body", {})

        return {
            "_weapon": Equippable(
                owner=None, config=random.choice(weapons[role.value])
            ),
            "_helmet": Equippable(
                owner=None, config=random.choice(helmets[role.value])
            ),
            "_body": Equippable(owner=None, config=random.choice(bodies[role.value])),
        }

    return factory


class EquippableConfig(NamedTuple):
    name: str = ""
    slot: str = ""
    attack_verb: str = ""
    range: int = 0
    attacks: list[str] | None = None
    spells: list[str] | None = None
    fighter_affixes: list = []
    equipment_affixes: list = []
    stats: EquippableStats | None = None


# Example Configs
Helmet = EquippableConfig(
    name="helmet",
    slot="_helmet",
    fighter_affixes=[PercentPowerIncrease],
    stats=EquippableStats(
        crit=0,
        block=0,
        evasion=0,
    ),
)

Breastplate = EquippableConfig(
    name="breastplate",
    slot="_body",
    fighter_affixes=[RawPowerIncrease, RawDefenceIncrease],
    equipment_affixes=[PercentCritIncrease],
    stats=EquippableStats(
        crit=0,
        block=0,
        evasion=0.05,
    ),
)

Sword = EquippableConfig(
    name="sword",
    slot="_weapon",
    attack_verb="melee",
    range=1,
    attacks=[NormalAttack.name],
    spells=[],
    fighter_affixes=[RawPowerIncrease],
    equipment_affixes=[PercentCritIncrease],
    stats=EquippableStats(
        crit=10,
        block=0,
        evasion=0,
        attack_dice=2,
        attack_dice_faces=6,
    ),
)

Bow = EquippableConfig(
    name="bow",
    slot="_weapon",
    attack_verb="ranged",
    range=5,
    attacks=[NormalAttack.name],
    
    spells=[],
    stats=EquippableStats(
        crit=15,
        block=0,
        evasion=0,
        attack_dice=1,
        attack_dice_faces=12,
    ),
)

SpellBook = EquippableConfig(
    name="grimoire",
    slot="_weapon",
    attack_verb="melee",
    range=1,
    attacks=[NormalAttack.name],
    spells=[MagicMissile.name, Shield.name, Fireball.name],
    stats=EquippableStats(
        crit=0,
        block=0,
        evasion=0,
        attack_dice=1,
        attack_dice_faces=4,
    ),
)
