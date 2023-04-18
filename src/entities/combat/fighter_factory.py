from copy import deepcopy
from random import randint
from typing import Callable, NamedTuple, Self

from src.config.constants import merc_names
from src.entities.ai.ai import BasicCombatAi, NoCombatAI
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name, Species
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.entities.sprites import EntitySprite
from src.gui.animated_sprite_config import (
    AnimatedSpriteConfig,
    choose_boss_texture,
    choose_goblin_textures,
    choose_merc_textures,
    choose_slime_textures,
)
from src.utils.proc_gen import syllables


class FactoryConfigurationError(ValueError):
    @classmethod
    def missing_mob_species(cls, species: str) -> Self:
        return cls(
            f"Could not choose sprite animation frames for character {species=}. Available species are "
            f"{', '.join([*MOB_TEXTURE_MAPPING.keys()])}"
        )


NAME_GENS: dict[str, Callable[[], str]] = {
    Species.GOBLIN: lambda: (
        f"{syllables.maybe_punctuated_name(max_syls=2)} {syllables.maybe_punctuated_name(max_syls=2)}"
    ),
    Species.SLIME: lambda: f"{syllables.simple_word(max_syls=2)}",
}


def gen_name(species: str) -> str:
    return NAME_GENS.get(species, lambda: f"{species}: '{syllables.simple_word()}'")()


Factory = Callable[[str], Entity]


class StatBlock(NamedTuple):
    hp: tuple[int, int]
    defence: tuple[int, int]
    power: tuple[int, int]
    is_enemy: bool
    speed: int
    is_boss: bool = False
    species: str = "human"

    @property
    def factory(self) -> Factory:
        return get_fighter_factory(self)

    def fighter_conf(self) -> dict:
        return {
            "hp": randint(*self.hp),
            "defence": randint(*self.defence),
            "power": randint(*self.power),
            "is_enemy": self.is_enemy,
            "speed": self.speed,
            "is_boss": self.is_boss,
        }


_mercenary = StatBlock(
    hp=(25, 25), defence=(1, 3), power=(3, 5), speed=3, is_enemy=False, is_boss=False
)
_monster = StatBlock(
    species=Species.SLIME,
    hp=(8, 8),
    defence=(1, 3),
    power=(1, 3),
    speed=1,
    is_enemy=True,
    is_boss=False,
)
_goblin = StatBlock(
    species=Species.GOBLIN,
    hp=(10, 14),
    defence=(1, 3),
    power=(2, 4),
    speed=2,
    is_enemy=True,
    is_boss=False,
)
_boss = StatBlock(
    hp=(30, 30), defence=(2, 4), power=(2, 4), speed=1, is_enemy=True, is_boss=True
)

MOB_TEXTURE_MAPPING = {
    Species.GOBLIN: choose_goblin_textures,
    Species.SLIME: choose_slime_textures,
}


def select_textures(species: str, fighter: Fighter) -> AnimatedSpriteConfig:
    """
    Set up textures for the fighter.
    As we have the name already, use that to determine particular enemy textures for hostile fighters.
    """
    if not fighter.is_enemy:
        return choose_merc_textures()

    elif fighter.is_boss:
        return choose_boss_texture()
    else:
        choose_mob_textures = MOB_TEXTURE_MAPPING.get(species)
        if choose_mob_textures is None:
            raise FactoryConfigurationError.missing_mob_species(species)

        return choose_mob_textures()


def get_fighter_factory(stats: StatBlock, attach_sprites: bool = True) -> Factory:
    def _from_conf(fighter_conf: dict, entity: Entity) -> Fighter:
        return Fighter(**fighter_conf).set_owner(owner=entity)

    def _create_entity(first_name, title, last_name) -> Entity:
        return Entity(
            name=Name(title=title, first_name=first_name, last_name=last_name),
            cost=randint(1, 5),
            species=stats.species,
        )

    def _attach_sprites(entity: Entity) -> Entity:
        sprite_config = select_textures(entity.species, entity.fighter)
        entity.set_entity_sprite(
            EntitySprite(
                idle_textures=sprite_config.idle_textures,
                attack_textures=sprite_config.attack_textures,
            )
        )

        return entity

    def factory(name=None, title=None, last_name=None):
        name = name or gen_name(stats.species)
        entity = _create_entity(name, title, last_name)

        conf = stats.fighter_conf()

        entity.fighter = _from_conf(conf, entity)

        entity.inventory = Inventory(owner=entity, capacity=1)

        if not entity.fighter.is_enemy:
            entity.inventory.add_item_to_inventory(HealingPotion(owner=entity))
        else:
            entity.ai = BasicCombatAi(owner=entity)

        if attach_sprites:
            entity = _attach_sprites(entity)

        return entity

    return factory


create_random_fighter = _mercenary.factory
create_random_monster = _monster.factory
create_random_goblin = _goblin.factory
create_random_boss = _boss.factory


class RecruitmentPool:
    def __init__(self, size: int = None) -> None:
        self.size = size
        self.pool: list[Entity] = []

    def increase_pool_size(self, new_size: int) -> None:
        # Set the new pool size and clear the previous pool
        self.size = new_size
        self.pool = []
        # Refill the pool with new recruits
        if self.size <= len(merc_names):
            self.fill_pool()

        else:
            raise ValueError(
                f"Not enough names for recruits. size: {self.size} < names: {len(merc_names)}"
            )

    def fill_pool(self) -> None:
        # Create a deepcopy of name array for consuming with pop.
        name_choices = deepcopy(merc_names)

        for _ in range(self.size):
            # iteratively pop a random name from the deepcopy array and supply the name to the factory.
            name = name_choices.pop(randint(0, len(name_choices) - 1))
            self.pool.append(create_random_fighter(name))

    def show_pool(self) -> None:
        # Sanity check function
        print(self.pool)
        for i in self.pool:
            print(i.fighter.hp)
