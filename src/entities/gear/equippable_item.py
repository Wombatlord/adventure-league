from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING, NamedTuple, Self

from src import config
from src.entities.combat.damage import Damage
from src.entities.combat.modifiable_stats import ModifiableStats, Modifier
from src.entities.combat.stats import EquippableItemStats, FighterStats, StatAffix
from src.entities.combat.weapon_attacks import WeaponAttackMeta
from src.entities.magic.spells import Spell, SpellMeta
from src.entities.properties.meta_compendium import MetaCompendium
from src.entities.sprites import AnimatedSpriteAttribute, SimpleSpriteAttribute
from src.gui.simple_sprite_config import choose_item_texture
from src.textures.texture_data import SpriteSheetSpecs
from src.utils.dice import D

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


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


tex = SpriteSheetSpecs.icons.load_one(108)


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
        self._sprite = SimpleSpriteAttribute(
            path_or_texture=choose_item_texture(self), scale=6
        )
        self._sprite.owner = self

        self._modifiable_stats = ModifiableStats(EquippableItemStats, self._stats)
        self._available_attacks_cache = []
        self._available_spells_cache = []
        self._init_affixes()

    def display_stats(self, delim=" | "):
        return self._stats.display_stats(delim)

    @property
    def sprite(self) -> AnimatedSpriteAttribute:
        return self._sprite

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

    def emit_damage(self) -> Damage:
        dies = int(self.stats.attack_dice)
        faces = int(self.stats.attack_dice_faces)
        roll_base_damage = dies * D(faces).roll()
        max_damage = self._owner.modifiable_stats.current.power + roll_base_damage

        return Damage(
            originator=self._owner,
            raw_damage=max_damage,
            crit_chance=self._owner.gear.modifiable_equipped_stats.current.crit,
        )

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
        for affix in self._fighter_affixes:
            self._owner.modifiable_stats.remove(affix.modifier)

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
