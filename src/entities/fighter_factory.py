from src.entities.entity import Entity
from src.entities.fighter import Fighter
from random import randint


def create_random_fighter() -> Entity:
    rand = randint(1, 5)
    fighter = Fighter(rand, rand, rand)
    return Entity("NAME", cost=rand, fighter=fighter)


class EntityPool:
    def __init__(self, size: int = None) -> None:
        self.size = size
        self.pool = []

    def fill_pool(self):
        for _ in range(self.size):
            self.pool.append(create_random_fighter())

    def show_pool(self):
        print(self.pool)
        for i in self.pool:
            print(i.fighter.hp)
