from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING, Callable, NamedTuple, Self

from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.damage import Damage
from src.entities.combat.modifiable_stats import ModifiableStats, Modifier
from src.entities.combat.stats import (EquippableItemStats, FighterStats,
                                       StatAffix, percent_crit_increase,
                                       percent_power_increase,
                                       raw_defence_increase,
                                       raw_power_increase)
from src.entities.combat.weapon_attacks import NormalAttack, WeaponAttackMeta
from src.entities.magic.spells import (Fireball, MagicMissile, Shield, Spell,
                                       SpellMeta)
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


class EquippableItem(EquippableABC):
    _slot: str
    _name: str
    _range: int
    _attack_verb: str
    _attacks: list[str]
    _spells: list[str]
    _fighter_affixes: list[StatAffix]
    _equippable_item_affixes: list[StatAffix]
    _available_attacks_cache: list[WeaponAttackMeta]
    _available_spells_cache: list[Spell]
    _modifiable_stats: ModifiableStats

    def __init__(
        self, owner: Fighter | None, config: EquippableItemConfig | None = None
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
        self._equippable_item_affixes = config.equippable_item_affixes
        self._stats = config.stats
        self._modifiable_stats = ModifiableStats(EquippableItemStats, self._stats)
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
        for affix in self._equippable_item_affixes:
            mods.append(affix())
        self._equippable_item_affixes = mods

    def _init_fighter_affixes(self):
        mods = []
        for affix in self._fighter_affixes:
            mods.append(affix())
        self._fighter_affixes = mods

    def fighter_modifiers(self) -> list[Modifier[FighterStats]]:
        return [affix.modifier for affix in self._fighter_affixes]

    def equipment_modifiers(self) -> list[Modifier[EquippableItemStats]]:
        return [affix.modifier for affix in self._equippable_item_affixes]


def default_equippable_item_factory(
    gearset_config: dict | None = None,
) -> Callable[[FighterArchetype], dict[str, EquippableItem]]:
    gearset_config = gearset_config or {
        "_weapon": {"melee": (sword,), "ranged": (bow,), "caster": (spellbook,)},
        "_helmet": {"melee": (helmet,), "ranged": (helmet,), "caster": (helmet,)},
        "_body": {
            "melee": (breastplate,),
            "ranged": (breastplate,),
            "caster": (breastplate,),
        },
    }

    def factory(role: FighterArchetype) -> dict[str, EquippableItem]:
        weapons = gearset_config.get("_weapon", {})
        helmets = gearset_config.get("_helmet", {})
        bodies = gearset_config.get("_body", {})

        return {
            "_weapon": EquippableItem(
                owner=None, config=random.choice(weapons[role.value])
            ),
            "_helmet": EquippableItem(
                owner=None, config=random.choice(helmets[role.value])
            ),
            "_body": EquippableItem(
                owner=None, config=random.choice(bodies[role.value])
            ),
        }

    return factory


class EquippableItemConfig(NamedTuple):
    name: str = ""
    slot: str = ""
    attack_verb: str = ""
    range: int = 0
    attacks: list[str] | None = None
    spells: list[str] | None = None
    fighter_affixes: list = []
    equippable_item_affixes: list = []
    stats: EquippableItemStats | None = None


class Configs:
    _items: list[EquippableItemConfig]

    def __init__(self, items):
        self._items = items

    def items_where(
        self, predicate: Callable[[EquippableItemConfig], bool]
    ) -> list[EquippableItemConfig]:
        return [item for item in self._items if predicate(item)]

    def __getattr__(self, name):
        return getattr(self._items, name)


item_configs = []


def register(conf: EquippableItemConfig) -> list[EquippableItemConfig]:
    global item_configs
    item_configs.append(conf)
    return item_configs


# Example Configs
helmet = register(
    EquippableItemConfig(
        name="helmet",
        slot="_helmet",
        fighter_affixes=[percent_power_increase],
        stats=EquippableItemStats(
            crit=0,
            block=0,
            evasion=0,
        ),
    )
)


breastplate = register(
    EquippableItemConfig(
        name="breastplate",
        slot="_body",
        fighter_affixes=[raw_power_increase, raw_defence_increase],
        equippable_item_affixes=[percent_crit_increase],
        stats=EquippableItemStats(
            crit=0,
            block=0,
            evasion=0.05,
        ),
    )
)

sword = register(
    EquippableItemConfig(
        name="sword",
        slot="_weapon",
        attack_verb="melee",
        range=1,
        attacks=[NormalAttack.name],
        spells=[],
        fighter_affixes=[raw_power_increase],
        equippable_item_affixes=[percent_crit_increase],
        stats=EquippableItemStats(
            crit=10,
            block=0,
            evasion=0,
            attack_dice=2,
            attack_dice_faces=6,
        ),
    )
)

bow = register(
    EquippableItemConfig(
        name="bow",
        slot="_weapon",
        attack_verb="ranged",
        range=5,
        attacks=[NormalAttack.name],
        spells=[],
        stats=EquippableItemStats(
            crit=15,
            block=0,
            evasion=0,
            attack_dice=1,
            attack_dice_faces=12,
        ),
    )
)

spellbook = register(
    EquippableItemConfig(
        name="grimoire",
        slot="_weapon",
        attack_verb="melee",
        range=1,
        attacks=[NormalAttack.name],
        spells=[MagicMissile.name, Shield.name, Fireball.name],
        stats=EquippableItemStats(
            crit=0,
            block=0,
            evasion=0,
            attack_dice=1,
            attack_dice_faces=4,
        ),
    )
)


def get_item_configs() -> Configs | list[EquippableItemConfig]:
    global item_configs
    return Configs([*item_configs])
