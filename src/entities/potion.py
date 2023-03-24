from src.entities.entity import Entity

class Potion:
    def __init__(self, name, potion_type):
        self.name = name
        self.potion_type = potion_type
    
    def drink(self):
        raise NotImplementedError


class HealingPotion(Potion):
    def __init__(self) -> None:
        super().__init__(
            name="Healing Potion",
            potion_type = "Healing"
        )
    
    def drink(self, owner: Entity):
        return {
            "heal": 5,
            "remove": self,
            "consumer": owner
        }