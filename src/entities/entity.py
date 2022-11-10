from typing import NamedTuple

class Name(NamedTuple):
    first_name: str = None
    title: str = None
    last_name: str = None

    def __str__(self) -> str:
        return " ".join(filter(lambda x: (x is not None), self))

    def name_and_title(self) -> str:
        if self.has_title():
            return f"{self.first_name.capitalize()} {self.title}"
        else:
            return f"{self.first_name.capitalize()}"

    def has_title(self) -> bool:
        return self.title is not None

    def formal_form(self) -> str:
        if not self.has_title:
            return "guv"
        else:
            return f"{self.first_name} {self.title}"

class Entity:
    def __init__(
        self,
        name: Name = None,
        cost: int = None,
        fighter=None,
        inventory=None,
        item=None,
        is_dead: bool = False,
    ) -> None:
        self.name = name
        self.cost = cost
        self.inventory = inventory
        self.item = item
        self.is_dead = is_dead

        # Entities with a fighter component can engage in combat.
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

    def get_dict(self) -> dict:
        # returns a dict for serialisation of an entity.
        result = {}

        result["name"] = self.name
        result["cost"] = self.cost

        if self.fighter:
            result["fighter"] = self.fighter.get_dict()

        if self.inventory:
            result["inventory"] = self.inventory.get_dict()

        if self.item:
            result["item"] = self.item

        return result
