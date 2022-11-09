from src.entities.entity import Entity
from src.entities.fighter import Fighter
from random import randint
from copy import deepcopy

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


def create_random_fighter(name) -> Entity:
    fighter = Fighter(randint(1, 5), randint(1, 5), randint(1, 5))
    return Entity(name, title='', cost=randint(1, 5), fighter=fighter)


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
