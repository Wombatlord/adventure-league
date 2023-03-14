from copy import deepcopy
from random import randint, choice
from typing import Callable, NamedTuple

from src.config.constants import merc_names, enemy_types
from src.gui.entity_texture_enums import *
from src.gui.window_data import WindowData
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.sprites import EntitySprite

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


_mercenary = StatBlock(
    hp=(25, 25), defence=(1, 3), power=(3, 5), speed=1, is_enemy=False, is_boss=False
)
_monster = StatBlock(hp=(10, 10), defence=(1, 3), power=(1, 3), speed=1, is_enemy=True, is_boss=False)
_boss = StatBlock(hp=(30, 30), defence=(2, 4), power=(2, 4), speed=1, is_enemy=True, is_boss = True)


def get_fighter_factory(stats: StatBlock) -> Factory:
    def _create_random_fighter(name=None, title=None, last_name=None) -> Entity:
        fighter = Fighter(
            hp=randint(*stats.hp),
            defence=randint(*stats.defence),
            power=randint(*stats.power),
            is_enemy=stats.is_enemy,
            speed=stats.speed,
            is_boss=stats.is_boss,
        )
        entity_name = Name(title=title, first_name=name, last_name=last_name)
        
        """
        Set up textures for the fighter.
        As we have the name already, use that to determine particular enemy textures for hostile fighters.
        """
        print(entity_name.name_and_title)
        match (fighter.is_enemy, fighter.is_boss):
            case (False, False):
                merc = choice([MercenaryOneTextures, MercenaryTwoTextures, MercenaryThreeTextures, MercenaryFourTextures])
                idle_textures, attack_textures = mercenary_textures(merc)
                
            case (True, False):
                if "Goblin" in  entity_name.name_and_title:
                    enemy = choice([GoblinOneTextures, GoblinTwoTextures, GoblinThreeTextures, GoblinFourTextures])
                    idle_textures, attack_textures = goblin_textures(enemy)
                
                if "Slime" in entity_name.name_and_title:
                    enemy = SlimeTexture
                    idle_textures, attack_textures = slime_textures(enemy)
            
            case (True, True):
                boss_type = randint(1, 3)
                if boss_type == 1:
                    boss = ImpTextures
                    idle_textures, attack_textures = boss_textures(boss)

                if boss_type == 2:
                    boss = ShadowTextures
                    idle_textures, attack_textures = boss_textures(boss)
                
                if boss_type == 3:
                    boss = LichTextures
                    idle_textures, attack_textures = boss_textures(boss)
        
        idle_one, idle_two = WindowData.fighters[idle_textures[0]], WindowData.fighters[idle_textures[1]]
        atk_one, atk_two = WindowData.fighters[attack_textures[0]], WindowData.fighters[attack_textures[1]]

        return Entity(sprite=EntitySprite(idle_textures=(idle_one, idle_two), attack_textures=(atk_one, atk_two)),name=entity_name, cost=randint(1, 5), fighter=fighter)

    return _create_random_fighter

def mercenary_textures(merc) -> tuple[tuple[int, int], tuple[int,int]]:
    if merc == MercenaryOneTextures:
        idle_textures = MercenaryOneTextures.idle_pair.value
        attack_textures = MercenaryOneTextures.attack_pair.value
            
    if merc == MercenaryTwoTextures:
        idle_textures = MercenaryTwoTextures.idle_pair.value
        attack_textures = MercenaryTwoTextures.attack_pair.value

    if merc == MercenaryThreeTextures:
        idle_textures = MercenaryThreeTextures.idle_pair.value
        attack_textures = MercenaryThreeTextures.attack_pair.value
            
    if merc == MercenaryFourTextures:
        idle_textures = MercenaryFourTextures.idle_pair.value
        attack_textures = MercenaryFourTextures.attack_pair.value
    
    return (idle_textures, attack_textures)

def goblin_textures(enemy) -> tuple[tuple[int, int], tuple[int,int]]:
    if enemy == GoblinOneTextures:
        idle_textures = GoblinOneTextures.idle_pair.value
        attack_textures = GoblinOneTextures.attack_pair.value
            
    if enemy == GoblinTwoTextures:
        idle_textures = GoblinTwoTextures.idle_pair.value
        attack_textures = GoblinTwoTextures.attack_pair.value

    if enemy == GoblinThreeTextures:
        idle_textures = GoblinThreeTextures.idle_pair.value
        attack_textures = GoblinThreeTextures.attack_pair.value
            
    if enemy == GoblinFourTextures:
        idle_textures = GoblinFourTextures.idle_pair.value
        attack_textures = GoblinFourTextures.attack_pair.value
    
    return (idle_textures, attack_textures)

def slime_textures(enemy) -> tuple[tuple[int, int], tuple[int, int]]:
    if enemy == SlimeTexture:
        idle_textures = SlimeTexture.idle_pair.value
        attack_textures = SlimeTexture.attack_pair.value
    
    return (idle_textures, attack_textures)

def boss_textures(boss) -> tuple[tuple[int,int], tuple[int,int]]:
    if boss == ImpTextures:
        idle_textures = ImpTextures.idle_pair.value
        attack_textures = ImpTextures.attack_pair.value
    
    if boss == ShadowTextures:
        idle_textures = ShadowTextures.idle_pair.value
        attack_textures = ShadowTextures.attack_pair.value
    
    if boss == LichTextures:
        idle_textures = LichTextures.idle_pair.value
        attack_textures = LichTextures.attack_pair.value    
    
    return (idle_textures, attack_textures)
    
create_random_fighter = _mercenary.factory
create_random_monster = _monster.factory
create_random_boss = _boss.factory


class EntityPool:
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
