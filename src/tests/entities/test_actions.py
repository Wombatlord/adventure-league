import unittest

from src.entities.actions import ActionCompendium
from src.entities.dungeon import Room
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.tests.fixtures import FighterFixtures


class ActionsTest(unittest.TestCase):
    @classmethod
    def get_entity(cls) -> Entity:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )

        return merc

    @classmethod
    def get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def set_up_encounter(cls, room_size: int, e1: Entity) -> Room:
        room = cls.get_encounter(room_size)
        room.add_entity(e1)

        e1.locatable.location = room.space.maxima.south.west
        return room

    def test_currently_available(self):
        # No assertion here, this is just so I could investigate what was coming out of: next(merc.fighter.request_action_choice())

        merc = self.get_entity()
        self.set_up_encounter(10, merc)
        event = next(merc.fighter.request_action_choice())
        breakpoint()
        # print(event)
