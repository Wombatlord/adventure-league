from src.entities.dungeon import Dungeon
from src.entities.fighter_factory import create_random_fighter


def create_random_dungeon(enemy_amount, dungeon_id) -> Dungeon:
    enemies = []
    for _ in range(enemy_amount):
        enemies.append(create_random_fighter("goblin"))

    return Dungeon(dungeon_id, enemies, "DESC", "TREASURE", 10)
