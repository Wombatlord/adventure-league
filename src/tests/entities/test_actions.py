import unittest

from src.entities.actions import (
    ActionCompendium,
    AttackAction,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.dungeon import Room
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.inventory import Inventory
from src.entities.items import HealingPotion
from src.tests.fixtures import FighterFixtures
from src.world.node import Node


class ActionsTest(unittest.TestCase):
    @classmethod
    def get_entities(cls) -> tuple[Entity, Entity]:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )
        merc.inventory = Inventory(owner=merc, capacity=1)
        enemy = Entity(
            name=Name(first_name="baby", last_name="weak", title="the feeble"),
            fighter=Fighter(**FighterFixtures.baby(enemy=True, boss=False)),
        )

        return merc, enemy

    @classmethod
    def get_potion(cls) -> HealingPotion:
        potion_entity = Entity()
        potion = HealingPotion(owner=potion_entity)
        return potion

    @classmethod
    def get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def set_up_encounter(cls, room_size: int, e1: Entity, e2) -> Room:
        room = cls.get_encounter(room_size)
        room.add_entity(e1)
        room.add_entity(e2)

        e1.locatable.location = room.space.minima.south.east
        e2.locatable.location = room.space.maxima.south.east
        return room

    def test_action_compendium_has_registered_all_actions(self):
        # Arrange
        keys = {"end turn", "attack", "consume item", "move"}
        actions = ActionCompendium.all_actions

        # Assert
        assert keys == {*actions.keys()}

        # Check each key contains the correct ActionMeta
        assert actions.get("end turn") is EndTurnAction
        assert actions.get("attack") is AttackAction
        assert actions.get("consume item") is ConsumeItemAction
        assert actions.get("move") is MoveAction

    def test_request_action_event_schema(self):
        # Arrange
        merc, enemy = self.get_entities()
        potion = self.get_potion()
        merc.inventory.add_item_to_inventory(potion)
        room = self.set_up_encounter(10, merc, enemy)
        merc.fighter.set_encounter_context(room)

        # Action
        event = next(merc.fighter.request_action_choice())

        # Assert
        assert isinstance(event, dict)
        assert isinstance(event["choices"], dict)
        choices = event.get("choices")

        for option_list in choices.values():
            for option in option_list:
                self._assert_schema(option)

    def _assert_schema(self, option: dict):
        assert type(option.get("name")) is str
        assert type(option.get("actor")) is Fighter
        assert type(option.get("cost")) is int
        assert callable(option.get("on_confirm"))

        destination = option.get("destination")
        assert destination is None or isinstance(
            destination, Node
        ), f"expected Node or None, got {type(destination)=}"

        path = option.get("path")
        assert path is None or isinstance(path, tuple)
        if path:
            assert all(isinstance(item, Node) for item in path)
