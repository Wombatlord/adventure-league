from random import randint
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter

boss_names = [
    "griffith",
    "grux",
    "kerax",
    "vestral",
    "xevrain",
    "selin",
    "kefka",
    "tristan",
]

boss_titles = [
    "the Terrible",
    "the Wicked",
    "the Dark Knight",
    "the Cleansing Flame",
    "the Crimson Promise",
    "the Broken Dreamer",
    "the Shattered Echo",
]

def create_random_monster(name) -> Entity:
    fighter = Fighter(10, randint(1, 3), randint(1, 3))
    entity_name = Name(title=None, first_name=name, last_name=None)
    return Entity(name=entity_name, cost=randint(1, 5), fighter=fighter)

def create_random_boss() -> Entity:
    fighter = Fighter(30, randint(2, 4), randint(2, 4))
    entity_name = Name(
        title=boss_titles[randint(0, len(boss_titles) - 1)],
        first_name=boss_names[randint(0, len(boss_names) - 1)],
        last_name=None,
    )
    return Entity(name=entity_name, fighter=fighter)
