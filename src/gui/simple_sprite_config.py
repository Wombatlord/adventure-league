from __future__ import annotations

import random
from typing import TYPE_CHECKING, NamedTuple, Sequence

from arcade import Texture

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem

from src.textures.texture_data import SpriteSheetSpecs


class SimpleSpriteConfig(NamedTuple):
    tex_idx: Sequence[int]

    @property
    def texture(self) -> Texture:
        return SpriteSheetSpecs.icons.load_one(self.tex_idx)


def choose_item_texture(item: EquippableItem):
    match item._slot:
        case "_weapon":
            if item._name == "sword":
                tx = random.choice(SWORDS)
            if item._name == "bow":
                tx = random.choice(BOWS)
            if item._name == "grimoire":
                tx = random.choice(STAVES)

        case "_helmet":
            tx = ARMOUR
        case "_body":
            tx = ARMOUR

    return tx.texture


ARMOUR = SimpleSpriteConfig(18)

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
