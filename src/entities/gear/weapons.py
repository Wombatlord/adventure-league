from typing import NamedTuple

from src.entities.combat.stats import (EquippableItemStats,
                                       percent_crit_increase,
                                       raw_power_increase)
from src.entities.combat.weapon_attacks import NormalAttack
from src.entities.gear.base_gear_names import BaseWeaponNames
from src.entities.gear.equippable_item import EquippableItemConfig
from src.entities.magic.spells import Fireball, MagicMissile, Shield

sword = EquippableItemConfig(
    name=BaseWeaponNames.SWORD,
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

bow = EquippableItemConfig(
    name=BaseWeaponNames.BOW,
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

spellbook = EquippableItemConfig(
    name=BaseWeaponNames.STAVE,
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
