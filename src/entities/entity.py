class Entity:
    def __init__(
        self,
        name: str = None,
        cost: int = None,
        fighter=None,
        inventory=None,
        item=None,
    ) -> None:
        self.name = name
        self.cost = cost
        self.inventory = inventory
        self.item = item

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
