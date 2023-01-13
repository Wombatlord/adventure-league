from src.entities.dungeon import Dungeon, Room
from src.config.constants import dungeon_descriptors, boss_titles, boss_names
from random import randint
from src.entities.fighter_factory import create_random_monster, create_random_boss


def describe_dungeon() -> str:
    descriptor_a = dungeon_descriptors.get("a")[
        randint(0, len(dungeon_descriptors["a"]) - 1)
    ]
    descriptor_b = dungeon_descriptors.get("b")[
        randint(0, len(dungeon_descriptors["b"]) - 1)
    ]
    return f"The {descriptor_a} {descriptor_b}"

def create_random_dungeon(enemy_amount, dungeon_id) -> Dungeon:
    enemies = []
    for i in range(enemy_amount):
        enemies.append(create_random_monster(f"goblin {i}", None))

    return Dungeon(
        dungeon_id,
        enemies,
        create_random_boss(
            name=boss_names[randint(0, len(boss_names) - 1)],
            title=boss_titles[randint(0, len(boss_titles) - 1)],
        ),
        describe_dungeon(),
        treasure=randint(100, 150),
        xp_reward=10,
    )


# Room testing with Room Class
def create_random_enemy_room(enemy_amount):
    room = Room()

    for enemy in range(enemy_amount):
        room.enemies.append(create_random_monster(f"goblin {enemy}", None))
    
    print(f"RandomEnemyRoom: {room.enemies}")
    return room


def create_random_boss_room():
    room = Room()

    room.enemies.append(
        create_random_boss(
            name=boss_names[randint(0, len(boss_names) - 1)],
            title=boss_titles[randint(0, len(boss_titles) - 1)],
        )
    )

    print(f"RandomBossRoom: {room.enemies}")
    return room


def rooms_test(room_amount):
    d = Dungeon(
        0,
        [],
        [],
        create_random_boss(
            name=boss_names[randint(0, len(boss_names) - 1)],
            title=boss_titles[randint(0, len(boss_titles) - 1)],
        ),
    )
    for _ in range(room_amount):
        d.rooms.append(create_random_enemy_room(enemy_amount=2))
    
    d.rooms.append(create_random_boss_room())

    print(f"{d.rooms=}")

    for i, _ in enumerate(d.rooms):
        print(f"{d.rooms[i].enemies=}")
