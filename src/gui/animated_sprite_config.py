import random
import select
from typing import NamedTuple, Self, Sequence

from arcade import Texture

from src.entities.combat.archetypes import FighterArchetype
from src.textures.texture_data import SheetSpec, SpriteSheetSpecs


class AnimatedSpriteConfig(NamedTuple):
    idle: Sequence[int]
    attack: Sequence[int]
    sheet_spec: SheetSpec = SpriteSheetSpecs.characters

    @property
    def idle_textures(self) -> tuple[Texture, ...]:
        return tuple(self.sheet_spec.load_one(idx) for idx in self.idle)

    @property
    def attack_textures(self) -> tuple[Texture, ...]:
        return tuple(self.sheet_spec.load_one(idx) for idx in self.attack)

    def get_normals(self) -> Self | None:
        if not (sheet_spec := self.sheet_spec.get_normals()):
            return None
            
        return AnimatedSpriteConfig(
            idle=self.idle, 
            attack=self.attack, 
            sheet_spec=sheet_spec,
        )

    def get_heights(self) -> Self | None:
        if not (sheet_spec := self.sheet_spec.get_height_map()):
            return None
        
        return AnimatedSpriteConfig(
            idle=self.idle,
            attack=self.attack,
            sheet_spec=sheet_spec,
        )


MERC_TEXTURE_OPTS = (
    AnimatedSpriteConfig(
        idle=(0, 1),
        attack=(2, 3),
    ),
    AnimatedSpriteConfig(
        idle=(8, 9),
        attack=(10, 11),
    ),
    AnimatedSpriteConfig(
        idle=(16, 17),
        attack=(18, 19),
    ),
    AnimatedSpriteConfig(
        idle=(24, 25),
        attack=(26, 27),
    ),
)


def choose_merc_textures(fighter) -> AnimatedSpriteConfig:
    match fighter.role:
        case FighterArchetype.MELEE:
            melee_opts = (MERC_TEXTURE_OPTS[0], MERC_TEXTURE_OPTS[3])
            return random.choice(melee_opts)

        case FighterArchetype.RANGED:
            return MERC_TEXTURE_OPTS[2]

        case FighterArchetype.CASTER:
            return MERC_TEXTURE_OPTS[1]


GOBLIN_TEXTURE_OPTS = [
    AnimatedSpriteConfig(
        idle=(32, 33),
        attack=(34, 35),
    ),
    AnimatedSpriteConfig(
        idle=(40, 41),
        attack=(42, 43),
    ),
    AnimatedSpriteConfig(
        idle=(48, 49),
        attack=(50, 51),
    ),
    AnimatedSpriteConfig(
        idle=(56, 57),
        attack=(58, 59),
    ),
]


def choose_goblin_textures() -> AnimatedSpriteConfig:
    return random.choice(GOBLIN_TEXTURE_OPTS)


SLIME_TEXTURE_OPTS = [
    AnimatedSpriteConfig(
        idle=(104, 105),
        attack=(106, 107),
    ),
]


def choose_slime_textures():
    return random.choice(SLIME_TEXTURE_OPTS)


SHADOW = AnimatedSpriteConfig(
    idle=(64, 65),
    attack=(66, 67),
)

LICH = AnimatedSpriteConfig(
    idle=(72, 73),
    attack=(74, 75),
)

IMP = AnimatedSpriteConfig(
    idle=(81, 82),
    attack=(83, 84),
)

BOSS_TEXTURE_OPTS = [
    SHADOW,
    LICH,
    IMP,
]


def choose_boss_texture() -> AnimatedSpriteConfig:
    return random.choice(BOSS_TEXTURE_OPTS)
