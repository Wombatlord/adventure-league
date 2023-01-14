from typing import NamedTuple, Optional

class Name(NamedTuple):
    first_name: str = None
    title: Optional[str] = None
    last_name: Optional[str] = None

    def __str__(self) -> str:
        return " ".join(filter(lambda x: (x is not None), self))

    @property
    def name_and_title(self) -> str:
        if self.has_title():
            return f"{self.first_name.capitalize()} {self.title}"
        else:
            return f"{self.first_name.capitalize()}"

    def has_title(self) -> bool:
        return self.title is not None


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
        self.on_death_hooks = []

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

    def die(self):
        for hook in self.on_death_hooks:
            hook(self)
