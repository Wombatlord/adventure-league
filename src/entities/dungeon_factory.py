from src.entities.dungeon import Dungeon
from random import randint
from src.entities.monster_factory import create_random_monster, create_random_boss

descriptors = {
    "a": [
        "Forgotten",
        "Haunted",
        "Forlorn",
        "Desolate",
        "Scourged",
        "Cursed",
        "Wailing",
        "Forsaken",
        "Scorched",
        "Frozen",
    ],
    "b": [
        "Crypt",
        "Church",
        "Cathedral",
        "Sepulcher",
        "Warcamp",
        "Cave",
        "Tunnels",
        "Mine",
        "Forest",
        "Lair",
    ],
}

def describe_dungeon() -> str:
    return f"The {descriptors.get('a')[randint(0, len(descriptors['a']) - 1)]} {descriptors.get('b')[randint(0, len(descriptors['b']) - 1)]}"

def create_random_dungeon(enemy_amount, dungeon_id) -> Dungeon:
    enemies = []
    for _ in range(enemy_amount):
        enemies.append(create_random_monster("goblin"))

    return Dungeon(dungeon_id, enemies, create_random_boss(), describe_dungeon(), "TREASURE", 10)
