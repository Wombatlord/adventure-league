from __future__ import annotations
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from random import randint
from copy import deepcopy
from typing import NamedTuple

names = [
    "guts",
    "raphael",
    "eliza",
    "vasquez",
    "seraph",
    "emilia",
    "roberto",
    "william",
    "beckett",
    "freya",
]

Factory = callable[[str], Entity]

class StatRange(NamedTuple):
    hp: tuple[int, int]
    defense: tuple[int, int]
    power: tuple[int, int]

    @property
    def factory(self) -> Factory:
        return get_fighter_factory(self)

_monster = StatRange(hp=(10, 10), defense=(0, 2), power=(1, 3))
_hero = StatRange(hp=(10, 10), defense=(0, 2), power=(1, 3))

class Splittable:
    def split(self) -> tuple[Splittable, Splittable]:
        ...

    def should_split(self) -> bool:
        ...


class Rect(Splittable):
    _parent_split: bool
    width: int
    height: int
    x: int
    y: int

    def __init__(self, *args):
        ...
        self._parent_split = args[-1]

    def should_split(self) -> bool:
        return self.height <= 1 or self.width <= 1

    def split(self, horizontal=None) -> tuple[Rect, Rect]:
        if horizontal is None:
            horizontal = not self._parent_split
        if horizontal:
            return (
                Rect(self.x, self.y, self.width, self.height/2, horizontal),
                Rect(self.x, self.y + self.height/2, self.width, self.height/2, horizontal)
            )
        else:
            ...


class BspNode:
    children: tuple[BspNode, BspNode] | None
    total: Splittable

    def __init__(self, total: Splittable):
        if randint(0, 1) and total.should_split():
            left, right = total.split()
            self.children = (BspNode(left), BspNode(right))
            self.total = None
        else:
            self.children = None
            self.total = total

    def get_contained(self) -> int:
        return self.total or sum(child.get_contained() for child in self.children)


def split(total) -> list[list|int]|int:
    if total > 1:
        if randint(0, 1):
            return [split(total/2), split(total - total/2)]
        else:
            return total
    
    return 1

def aggregate(tree: list[list|int]|int):
    if type(tree) is int:
        return tree

    left, right = tree
    return aggregate(left) + aggregate(right)
        




## ##
## ##
## 
## # #
   # #

def get_fighter_factory(stat_ranges: StatRange) -> Factory:
    """
    Takes a stat_ranges conguration
    """

    def create_random_fighter_(name: str) -> Entity:
        fighter = Fighter(
            hp=randint(*stat_ranges.hp), 
            defense=randint(*stat_ranges.defense), 
            power=randint(*stat_ranges.power),
        )
        entity_name = Name(title=None, first_name=name, last_name=None)
        return Entity(name=entity_name, cost=randint(1, 5), fighter=fighter)
    
    return create_random_fighter_

create_random_fighter = _hero.factory
create_random_monster = _monster.factory


class EntityPool:
    def __init__(self, size: int = None) -> None:
        self.size = size
        self.pool = []

    def increase_pool_size(self, new_size: int) -> None:
        # Set the new pool size and clear the previous pool
        self.size = new_size
        self.pool = []
        # Refill the pool with new recruits
        if self.size <= len(names):
            self.fill_pool()

        else:
            raise ValueError(
                f"Not enough names for recruits. size: {self.size} < names: {len(names)}"
            )

    def fill_pool(self) -> None:
        # Create a deepcopy of name array for consuming with pop.
        name_choices = deepcopy(names)

        for _ in range(self.size):
            # iteratively pop a random name from the deepcopy array and supply the name to the factory.
            name = name_choices.pop(randint(0, len(name_choices) - 1))
            self.pool.append(create_random_fighter(name))

    def show_pool(self) -> None:
        # Sanity check function
        print(self.pool)
        for i in self.pool:
            print(i.fighter.hp)
