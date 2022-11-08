from __future__ import annotations
from src.entities.entity import Entity
from random import randint

names = [
    "Band of the Hawk",
    "Diamond Dogs",
    "Screaming Eagles",
    "Order of the Hound",
    "Iron Bears",
]


class Guild:
    def __init__(
        self,
        name: str = None,
        level: int = None,
        funds: int = None,
        roster_limit: int = None,
        roster: list[Entity] = None,
    ) -> None:
        self.name = name
        self.level = level
        self.funds = funds
        self.roster_limit = roster_limit
        self.roster = roster
        self.roster_scalar = 1.5
        self.team = Team()

        if self.roster_limit == None:
            self.roster_limit = int(self.level * self.roster_scalar)

        if self.name == None:
            self.name = names.pop(randint(0, len(names) - 1))

    def recruit(self, i, pool) -> list[Entity]:
        if len(self.roster) >= self.roster_limit:
            print("Roster full.")
            return

        if pool[i].cost > self.funds:
            print(f"{pool[i].name.capitalize()} is too expensive.")
            return

        else:
            self.funds -= pool[i].cost
            choice = pool.pop(i)
            return self.roster.append(choice)

    def remove_from_roster(self, i):
        # Remove a member from the roster. For example, if killed in combat, call this.
        self.roster.pop(i)

class Team:
    def __init__(self) -> None:
        self.name = "TEAM"
        self.members: list[Entity] = []
    
    def get_team(self):
        return self.members

    def assign_to_team(self, roster, selection):
        self.members.append(roster[selection])

    def remove_from_team(self, selection):
        self.members.pop(selection)