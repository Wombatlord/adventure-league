from __future__ import annotations

from typing import TYPE_CHECKING, Self

from src.entities.sprites import SpriteAttribute

if TYPE_CHECKING:
    from src.entities.entity import Entity
    from src.entities.combat.fighter import Fighter
    from src.gui.animated_sprite_config import AnimatedSpriteConfig

from src.gui.animated_sprite_config import (
    choose_boss_texture,
    choose_goblin_textures,
    choose_merc_textures,
    choose_slime_textures,
)


class Species:
    GOBLIN = "goblin"
    SLIME = "slime"
    HUMAN = "human"


MOB_TEXTURE_MAPPING = {
    Species.GOBLIN: choose_goblin_textures,
    Species.SLIME: choose_slime_textures,
}


class FactoryConfigurationError(ValueError):
    @classmethod
    def missing_mob_species(cls, species: str) -> Self:
        return cls(
            f"Could not choose sprite animation frames for character {species=}. Available species are "
            f"{', '.join([*MOB_TEXTURE_MAPPING.keys()])}"
        )


def select_textures(species: str, fighter: Fighter) -> AnimatedSpriteConfig:
    """
    Set up textures for the fighter.
    As we have the name already, use that to determine particular enemy textures for hostile fighters.
    """
    if not fighter.is_enemy:
        return choose_merc_textures(fighter)

    elif fighter.is_boss:
        return choose_boss_texture()
    else:
        choose_mob_textures = MOB_TEXTURE_MAPPING.get(species)
        if choose_mob_textures is None:
            raise FactoryConfigurationError.missing_mob_species(species)

        return choose_mob_textures()


def attach_sprites(entity: Entity) -> Entity:
    sprite_config = select_textures(entity.species, entity.fighter)
    entity.set_entity_sprite(
        SpriteAttribute(
            idle_textures=sprite_config.idle_textures,
            attack_textures=sprite_config.attack_textures,
        )
    )

    return entity
