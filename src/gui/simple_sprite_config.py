from __future__ import annotations

import random
from typing import TYPE_CHECKING, NamedTuple, Sequence

from arcade import Texture
from src.entities.gear.base_gear_names import BaseWeaponNames

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem

from src.textures.texture_data import SpriteSheetSpecs


class SimpleSpriteConfig(NamedTuple):
    tex_idx: int

    @property
    def texture(self) -> Texture:
        return SpriteSheetSpecs.icons.load_one(self.tex_idx)


def choose_item_texture(item: EquippableItem) -> Texture:
    match item._slot:
        case "_weapon":
            if item._name == BaseWeaponNames.SWORD:
                tx = random.choice(SWORDS)
            if item._name == BaseWeaponNames.BOW:
                tx = random.choice(BOWS)
            if item._name == BaseWeaponNames.STAVE:
                tx = random.choice(STAVES)

        case "_helmet":
            tx = HELMET
        case "_body":
            tx = ARMOUR

    return tx.texture


ARMOUR = SimpleSpriteConfig(84)

HELMET = SimpleSpriteConfig(85)

SWORDS = (
    SimpleSpriteConfig(58),
    SimpleSpriteConfig(68),
    SimpleSpriteConfig(78),
    SimpleSpriteConfig(88),
    SimpleSpriteConfig(98),
    SimpleSpriteConfig(108),
)

STAVES = (
    SimpleSpriteConfig(57),
    SimpleSpriteConfig(67),
    SimpleSpriteConfig(77),
    SimpleSpriteConfig(87),
    SimpleSpriteConfig(97),
    SimpleSpriteConfig(107),
)

BOWS = (
    SimpleSpriteConfig(59),
    SimpleSpriteConfig(69),
    SimpleSpriteConfig(79),
    SimpleSpriteConfig(89),
    SimpleSpriteConfig(99),
    SimpleSpriteConfig(109),
)
