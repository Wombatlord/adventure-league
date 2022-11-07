from src.entities.entity import Entity


class Guild:
    def __init__(
        self,
        name: str = None,
        level: int = None,
        funds: int = None,
        roster: list[Entity] = None,
    ) -> None:
        self.name = name
        self.level = level
        self.funds = funds
        self.roster = roster

    def recruit(self, i, pool) -> list[Entity]:
        if pool[i].cost <= self.funds:
            self.funds -= pool[i].cost
            choice = pool.pop(i)
            return self.roster.append(choice)

        else:
            print("Too expensive.")
