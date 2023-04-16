import unittest

from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.tests.fixtures import FighterFixtures


class HealingPotionTest(unittest.TestCase):
    @classmethod
    def get_entity_with_inventory(cls, inventory_capacity) -> Entity:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )
        merc.inventory = Inventory(owner=merc, capacity=inventory_capacity)

        return merc

    @classmethod
    def get_potion(cls) -> HealingPotion:
        potion_entity = Entity()
        potion = HealingPotion(owner=potion_entity)
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

    def test_potion_in_inventory_is_drinkable_by_owning_entity_with_inventory(self):
        # Arrange
        merc = self.get_entity_with_inventory(inventory_capacity=1)
        merc.fighter.hp -= 5

        potion_1 = self.get_potion()

        # Action
        merc.inventory.add_item_to_inventory(potion_1)
        event = next(merc.fighter.consume_item(potion_1))

        # Assert
        assert potion_1 not in merc.inventory, f"{merc.inventory.items}"
        assert (
            merc.fighter.hp == merc.fighter.max_hp
        ), f"expected {merc.fighter.hp=} {merc.fighter.max_hp=}"
        expected = merc.annotate_event(
            {
                "message": f"{potion_1.get_name()} used by {merc.inventory.owner.name}",
                "item_consumed": {
                    "consumable": potion_1,
                    "effect": {
                        "name": potion_1.get_consume_effect_name(),
                        "target": potion_1.owner,
                        "details": {"heal_amount": 5},
                    },
                },
            }
        )
        assert event == expected, f"{event=}\n\n{expected=}"
