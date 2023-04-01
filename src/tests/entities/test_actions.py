import unittest

from src.entities.actions import ActionCompendium, EndTurnAction, AttackAction, ConsumeItemAction, MoveAction
from src.entities.inventory import Inventory
from src.entities.items import HealingPotion
from src.entities.dungeon import Room
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.world.node import Node
from src.tests.fixtures import FighterFixtures

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
        keys = ["end turn", "attack", "consume_item", "move"]

        # Assert
        for k in keys:
            assert k in ActionCompendium.all_actions.keys() # Check all expected keys are contained in the ActionCompendium.all_actions
        
        for k, v in ActionCompendium.all_actions.items(): # Check each key contains the correct ActionMeta
            if k == "end turn":
                assert v == EndTurnAction
            
            if k =="attack":
                assert v == AttackAction
                
            if k == "consume_item":
                assert v == ConsumeItemAction
                
            if k == "move":
                assert v == MoveAction
            
        
    def test_action_schema(self):
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
        assert isinstance(event['choices'], dict)

        for v in event['choices'].values(): # Traverse the object graph to check values associated to keys are of the correct Type.
            for k in v:
                if k == 'name': # The name of the ActionType
                    assert isinstance(v, str)
                
                if k == 'actor': # The Fighter to which the actions are available
                    assert isinstance(v, Fighter)
                
                if k == 'cost': # The cost of a particular action
                    assert isinstance(v, int)
                
                if k == 'on_confirm': # The callable to be invoked to carry out the action
                    assert callable(v)
                
                if k == 'destination': # The destination associated to a particular Move Action
                    assert isinstance(v, Node)
                
                if k == 'path': # The path to a particular Move Action's destination.
                    assert isinstance(v, tuple[Node])
        