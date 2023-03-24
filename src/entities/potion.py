from src.engine.engine import Action
from src.entities.entity import Entity


class Potion:
    def __init__(self, name, potion_type):
        self.name = name
        self.potion_type = potion_type

    def drink(self):
        raise NotImplementedError


class HealingPotion(Potion):
    def __init__(self) -> None:
        super().__init__(name="Healing Potion", potion_type="Healing")
        self.heal_amount = 5

    def drink(self, target: Entity, owner: Entity) -> Action:
        if target.fighter.hp < target.fighter.max_hp:
            target.fighter.hp += self.heal_amount
            owner.inventory.remove_item(self)

        return {
            "message": f"{self.name} used by {owner}",
            "potion_used": {
                "effect": {
                    "heal": self.heal_amount,
                    "target": target,
                },
                "used_by": {
                    "item": self,
                    "owner": owner,
                },
            },
            "entity_data": {
                "health": target.fighter.hp if target.fighter else None,
                "name": target.name.name_and_title,
                "retreat": target.fighter.retreating,
                "species": target.species,
            },
        }
