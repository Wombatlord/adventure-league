import unittest
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.tests.fixtures import FighterFixtures
from src.entities.potion import HealingPotion
from src.entities.inventory import Inventory


class InventoryTest(unittest.TestCase):
    
    @classmethod
    def get_entity_with_inventory(cls, inventory_capacity) -> Entity:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
            inventory=Inventory(capacity=inventory_capacity)
        )

        return merc
    
    @classmethod
    def get_potion(cls) -> HealingPotion:
        potion = HealingPotion()
        return potion
    
    def test_entity_has_an_inventory(self):
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        assert merc.inventory is not None
        assert isinstance(merc.inventory, Inventory)
        assert len(merc.inventory.items) == 1
    
    def test_item_is_added_to_an_entities_inventory(self):
        # Arrange
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        potion = self.get_potion()
        
        # Action
        merc.inventory.add_item_to_inventory(potion)
        
        # Assert
        assert merc.inventory.items[0] is potion
    
    def test_items_are_not_added_beyond_inventory_capacity(self):
        # Arrange
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        potion_1 = self.get_potion()
        potion_2 = self.get_potion()
        
        # Action
        merc.inventory.add_item_to_inventory(potion_1)
        merc.inventory.add_item_to_inventory(potion_2)
        
        # Assert
        assert merc.inventory.items[0] is potion_1
        assert potion_2 not in merc.inventory.items
    
    def test_item_is_removed_from_inventory(self):
        # Arrange
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        potion_1 = self.get_potion()
        
        # Action
        merc.inventory.add_item_to_inventory(potion_1)
        merc.inventory.remove_item(potion_1)
        
        # Assert
        assert potion_1 not in merc.inventory.items
        assert merc.inventory.items[0] is None
    
    def test_item_in_inventory_is_usable_by_entity_with_inventory(self):
        # Arrange
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        potion_1 = self.get_potion()
        
        # Action
        merc.inventory.add_item_to_inventory(potion_1)
        event = merc.inventory.items[0].drink(owner=merc)
        
        # Assert
        assert event == {"heal": 5, "remove": potion_1, "consumer": merc}