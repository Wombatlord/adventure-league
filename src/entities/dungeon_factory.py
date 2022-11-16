from src.entities.dungeon import Dungeon
from src.entities.fighter_factory import create_random_fighter, create_random_boss


def create_random_dungeon(enemy_amount, dungeon_id) -> Dungeon:
    enemies = []
    for _ in range(enemy_amount):
        enemies.append(create_random_fighter("goblin"))

    boss = create_random_boss()

    return Dungeon(dungeon_id, enemies, boss, "DESC", "TREASURE", 10)
