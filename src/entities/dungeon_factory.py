from random import choice, randint

from src.config.constants import (
    boss_names,
    boss_titles,
    dungeon_descriptors,
    enemy_types,
)
from src.entities.dungeon import Dungeon, Room
from src.entities.fighter_factory import (
    create_random_boss,
    create_random_goblin,
    create_random_monster,
)


def describe_dungeon() -> str:
    descriptor_a = dungeon_descriptors.get("a")[
        randint(0, len(dungeon_descriptors["a"]) - 1)
    ]
    descriptor_b = dungeon_descriptors.get("b")[
        randint(0, len(dungeon_descriptors["b"]) - 1)
    ]
    return f"The {descriptor_a} {descriptor_b}"


def create_random_dungeon(enemy_amount) -> Dungeon:
    enemies = []
    for i in range(enemy_amount):
        enemies.append(create_random_monster(f"{choice(enemies)} {i}", None))

    return Dungeon(
        0,
        [],
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
def create_random_enemy_room(enemy_amount) -> Room:
    room = Room()

    for enemy in range(enemy_amount):
        roll = randint(0, 3)
        if roll > 2:
            room.add_entity(create_random_goblin())
        else:
            room.add_entity(create_random_monster())

    return room


def create_random_boss_room() -> Room:
    room = Room()

    room.add_entity(
        create_random_boss(
            name=boss_names[randint(0, len(boss_names) - 1)],
            title=boss_titles[randint(0, len(boss_titles) - 1)],
        )
    )
    return room


def create_dungeon_with_boss_room(max_enemies_per_room, room_amount: int) -> Dungeon:
    d = Dungeon(
        max_enemies_per_room,
        [],
        [],
        None,
        describe_dungeon(),
        treasure=randint(100, 150),
        xp_reward=10,
    )
    for _ in range(room_amount):
        e = randint(1, d.max_enemies_per_room)
        d.rooms.append(create_random_enemy_room(enemy_amount=e))

    d.rooms.append(create_random_boss_room())
    d.boss = d.rooms[-1].enemies[0]
    return d

    # print(f"{d.rooms=}")

    # for i, _ in enumerate(d.rooms):
    #     print(f"{d.rooms[i].enemies=}")
