from copy import deepcopy
from random import randint
from typing import Callable, NamedTuple

from src.config.constants import merc_names
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter

Factory = Callable[[str], Entity]


class StatBlock(NamedTuple):
    hp: tuple[int, int]
    defence: tuple[int, int]
    power: tuple[int, int]
    is_enemy: bool
    speed: int

    @property
    def factory(self) -> Factory:
        return get_fighter_factory(self)


_mercenary = StatBlock(
    hp=(25, 25), defence=(1, 3), power=(3, 5), speed=1, is_enemy=False
)
_monster = StatBlock(hp=(10, 10), defence=(1, 3), power=(1, 3), speed=1, is_enemy=True)
_boss = StatBlock(hp=(30, 30), defence=(2, 4), power=(2, 4), speed=1, is_enemy=True)


def get_fighter_factory(stats: StatBlock) -> Factory:
    def _create_random_fighter(name=None, title=None, last_name=None) -> Entity:
        fighter = Fighter(
            hp=randint(*stats.hp),
            defence=randint(*stats.defence),
            power=randint(*stats.power),
            is_enemy=stats.is_enemy,
            speed=stats.speed,
        )
        entity_name = Name(title=title, first_name=name, last_name=last_name)
        return Entity(name=entity_name, cost=randint(1, 5), fighter=fighter)

    return _create_random_fighter


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
