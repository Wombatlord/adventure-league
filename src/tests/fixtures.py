import random
from typing import Callable
from src.engine.guild import Guild

from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name
from src.entities.item.equipment import Equipment
from src.entities.item.equippable import Equippable, Sword, default_equippable_factory
from src.entities.item.items import HealingPotion
from src.utils.proc_gen.syllables import simple_word
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
    
    @staticmethod
    def gandalf(enemy=False, boss=False):
        return {
            "hp": 20,
            "defence": 5,
            "power": 1,
            "role": FighterArchetype.CASTER,
            "is_enemy": enemy,
            "speed": 1,
            "is_boss": boss,
        }
    
    @staticmethod
    def legolas(enemy=False, boss=False):
        return  {
            "hp": 15,
            "defence": 3,
            "power": 3,
            "role": FighterArchetype.RANGED,
            "is_enemy": enemy,
            "speed": 4,
            "is_boss": boss,
        }


def _nth(n):
    suffix = "th"
    match n % 10, n % 100:
        case 3, x if x != 13:
            suffix = "rd"
        case 2, x if x != 12:
            suffix = "nd"
        case 1, x if x != 11:
            suffix = "st"

    return f"{n}{suffix}"


class EntityFactory:
    @classmethod
    def make_strongs(cls, enemy: bool, count=1) -> Entity:
        e = Entity(
            name=Name(
                first_name="strong", last_name="tactical", title=f"the {_nth(count)}"
            ),
            fighter=Fighter(**FighterFixtures.strong(enemy=enemy, boss=False)),
        ).with_inventory_capacity(1)
        weapon = Equippable(None, Sword)
        e.fighter.equipment = Equipment(e.fighter)
        e.fighter.equipment.equip_item(weapon)
        return e
    
    @classmethod
    def make_babies(cls, enemy: bool, count=1) -> Entity:
        e = Entity(
            name=Name(
                first_name="baby", last_name="feeble", title=f"the {_nth(count)}"
            ),
            fighter=Fighter(**FighterFixtures.baby(enemy=enemy, boss=False)),
        ).with_inventory_capacity(1)
        weapon = Equippable(None, Sword)
        e.fighter.equipment = Equipment(e.fighter)
        e.fighter.equipment.equip_item(weapon)
        return e
    
    @classmethod
    def from_fixture(cls, fixture: Callable[[bool], dict], enemy=False, count=1) -> list[Entity]:
        entities = []
        for _ in range(count):
            name = Name(first_name=simple_word(min_syls=2, max_syls=3), last_name=simple_word(min_syls=2, max_syls=3), title="")
            e = Entity(
                name=name,
                fighter=Fighter(**fixture(enemy))
            ).with_inventory_capacity(1)
            e.fighter.equipment = Equipment(e.fighter)
            factory = default_equippable_factory()
            gear = factory(e.fighter.role)
            for item in gear.values():
                e.fighter.equipment.equip_item(item)

            entities.append(e)

        return entities



class EncounterFactory:
    @classmethod
    def _make_team(cls, strong_count=0, baby_count=0, enemy=False) -> list[Entity]:
        team = []
        for i in range(strong_count):
            team.append(EntityFactory.make_strongs(enemy=enemy, count=i + 1))

        for i in range(baby_count):
            team.append(EntityFactory.make_babies(enemy=enemy, count=i + 1))

        return team

    @classmethod
    def _get_entities(cls) -> tuple[Entity, Entity]:
        merc = EntityFactory.make_strongs(enemy=False)
        enemy = EntityFactory.make_babies(enemy=True)

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



class GuildFactory:
    @classmethod
    def make_guild(cls) -> Guild:
        guild = Guild(
            name="TEST GUILD",
            xp=4000,
            funds=100,
            roster=[],
        )

        guild.roster = [
            *EntityFactory.from_fixture(FighterFixtures.strong),
            *EntityFactory.from_fixture(FighterFixtures.gandalf),
            *EntityFactory.from_fixture(FighterFixtures.legolas)
        ]

        guild.team.assign_to_team(guild.roster[0])
        guild.team.assign_to_team(guild.roster[1])

        return guild

