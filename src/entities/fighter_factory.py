from copy import deepcopy
from random import choice, randint
from typing import Callable, NamedTuple

from src.config.constants import merc_names
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.sprites import EntitySprite
from src.gui.entity_texture_enums import *
from src.gui.window_data import WindowData

MERC_TEXTURES = [
    MercenaryOneTextures,
    MercenaryTwoTextures,
    MercenaryThreeTextures,
    MercenaryFourTextures,
]

LICH_TEXTURES = [
    ImpTextures,
    ShadowTextures,
    LichTextures,
]

SLIME_TEXTURES = [SlimeTexture]

GOBLIN_TEXTURES = [
    GoblinOneTextures,
    GoblinTwoTextures,
    GoblinThreeTextures,
    GoblinFourTextures,
]

Factory = Callable[[str], Entity]


class StatBlock(NamedTuple):
    hp: tuple[int, int]
    defence: tuple[int, int]
    power: tuple[int, int]
    is_enemy: bool
    speed: int
    is_boss: bool = False

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
    hp=(10, 10), defence=(1, 3), power=(1, 3), speed=1, is_enemy=True, is_boss=False
)
_boss = StatBlock(
    hp=(30, 30), defence=(2, 4), power=(2, 4), speed=1, is_enemy=True, is_boss=True
)


def select_textures(entity_name, fighter):
    """
    Set up textures for the fighter.
    As we have the name already, use that to determine particular enemy textures for hostile fighters.
    """
    texture_opts = MERC_TEXTURES
    match (fighter.is_enemy, fighter.is_boss):
        case (True, False):
            if "Goblin" in entity_name.name_and_title:
                texture_opts = GOBLIN_TEXTURES
            elif "Slime" in entity_name.name_and_title:
                texture_opts = SLIME_TEXTURES

        case (True, True):
            texture_opts = LICH_TEXTURES

    idle_textures, attack_textures = unpack_tex(choice(texture_opts))

    idle_one, idle_two, atk_one, atk_two = tuple(
        map(lambda tex: WindowData.fighters[tex], idle_textures + attack_textures),
    )

    return atk_one, atk_two, idle_one, idle_two


def get_fighter_factory(stats: StatBlock, attach_sprites: bool = True) -> Factory:
    conf = {
        "hp": randint(*stats.hp),
        "defence": randint(*stats.defence),
        "power": randint(*stats.power),
        "is_enemy": stats.is_enemy,
        "speed": stats.speed,
        "is_boss": stats.is_boss,
    }

    def _from_conf(fighter_conf: dict, entity: Entity) -> Fighter:
        fighter = Fighter(**fighter_conf)
        fighter.owner = entity
        return fighter

    def _create_entity(first_name, last_name, title) -> Entity:
        return Entity(
            name=Name(title=title, first_name=first_name, last_name=last_name),
            cost=randint(1, 5),
        )

    def _attach_sprites(entity: Entity) -> Entity:
        if entity.fighter is None:
            breakpoint()

        atk_one, atk_two, idle_one, idle_two = select_textures(
            entity.name, entity.fighter
        )
        entity.set_entity_sprite(
            EntitySprite(
                idle_textures=(idle_one, idle_two), attack_textures=(atk_one, atk_two)
            )
        )

        return entity

    def factory(name=None, title=None, last_name=None):
        entity = _create_entity(name, title, last_name)
        entity.fighter = _from_conf(conf, entity)
        if attach_sprites:
            entity = _attach_sprites(entity)

        return entity

    return factory


def unpack_tex(tex_enum) -> tuple[tuple[int, int], tuple[int, int]]:
    return tex_enum.idle_pair.value, tex_enum.attack_pair.value


create_random_fighter = _mercenary.factory
create_random_monster = _monster.factory
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
