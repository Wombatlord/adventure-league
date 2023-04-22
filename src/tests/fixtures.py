import random
from typing import Callable

from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.utils.proc_gen.syllables import inoffensive
from src.world.level.room import Room
from src.world.node import Node


class FighterFixtures:
    @staticmethod
    def strong(enemy=False, boss=False):
        return {
            "hp": 100,
            "defence": 10,
            "is_enemy": enemy,
            "power": 10,
            "role": FighterArchetype.MELEE,
            "speed": 1,
            "is_boss": boss,
        }

    @staticmethod
    def baby(enemy=False, boss=False):
        return {
            "hp": 1,
            "defence": 0,
            "power": 0,
            "role": FighterArchetype.MELEE,
            "is_enemy": enemy,
            "speed": 1,
            "is_boss": boss,
        }


def _nth(n):
    suffix = "th"
    match n % 10, n % 100:
        case 3, _:
            suffix = "rd"
        case 2, x if x != 12:
            suffix = "nd"
        case 1, x if x != 11:
            suffix = "st"

    return f"{n}{suffix}"


class EncounterFactory:
    @classmethod
    def _make_strong(cls, enemy: bool, count=1) -> Entity:
        return Entity(
            name=Name(
                first_name="strong", last_name="tactical", title=f"the {_nth(count)}"
            ),
            fighter=Fighter(**FighterFixtures.strong(enemy=enemy, boss=False)),
        ).with_inventory_capacity(1)

    @classmethod
    def _make_baby(cls, enemy: bool, count=1) -> Entity:
        return Entity(
            name=Name(
                first_name="baby", last_name="feeble", title=f"the {_nth(count)}"
            ),
            fighter=Fighter(**FighterFixtures.baby(enemy=enemy, boss=False)),
        ).with_inventory_capacity(1)

    @classmethod
    def _make_team(cls, strong_count=0, baby_count=0, enemy=False) -> list[Entity]:
        team = []
        for i in range(strong_count):
            team.append(cls._make_strong(enemy=enemy, count=i + 1))

        for i in range(baby_count):
            team.append(cls._make_baby(enemy=enemy, count=i + 1))

        return team

    @classmethod
    def _get_entities(cls) -> tuple[Entity, Entity]:
        merc = cls._make_strong(enemy=False)
        enemy = cls._make_baby(enemy=True)

        return merc, enemy

    @classmethod
    def _get_potion(cls) -> HealingPotion:
        potion_entity = Entity()
        potion = HealingPotion(owner=potion_entity)
        return potion

    @classmethod
    def _get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def one_vs_one_enemies_lose(
        cls, room_size: int
    ) -> tuple[Room, list[Entity], list[Entity]]:
        room = cls._get_encounter(room_size)
        mercs = room.include_party(cls._make_team(strong_count=1, enemy=False))
        enemies = room.include_party(cls._make_team(baby_count=1, enemy=True))

        e1, e2 = mercs + enemies

        e1.locatable.location = room.space.minima
        e2.locatable.location = room.space.maxima - Node(1, 1)
        return room, mercs, enemies
