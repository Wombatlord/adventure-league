from __future__ import annotations
from src.config.constants import team_names
from src.entities.entity import Entity
from random import randint
from typing import Optional


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

        if self.roster_limit == None:
            self.roster_limit = int(self.level * self.roster_scalar)

        self.team = Team()
        if self.team:
            self.team.owner = self

    def get_dict(self) -> dict:
        guild = {}

        guild["name"] = self.name
        guild["level"] = self.level
        guild["funds"] = self.funds
        guild["roster_limit"] = self.roster_limit
        guild["roster"] = self.roster
        guild["roster_scalar"] = self.roster_scalar
        guild["team"] = self.team.get_dict()

        return guild

    def recruit(self, i, pool) -> list[Entity]:
        if len(self.roster) >= self.roster_limit:
            print("Roster full.")
            return

        if pool[i].cost > self.funds:
            print(f"{pool[i].name.first_name.capitalize()} is too expensive.")
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
        self.owner: Optional[Guild] = None
        self.name = None
        self.members: list[Entity] = []

    def name_team(self, name: str | None = None):
        if name == None:
            self.name = team_names.get(self.owner.name)[
                randint(0, len(team_names[self.owner.name]) - 1)
            ]
        else:
            self.name = name

    def get_dict(self) -> dict:
        team = {}

        team["name"] = self.name
        team["members"] = self.members

        return team

    def get_team(self):
        return self.members

    def assign_to_team(self, roster, selection):
        self.members.append(roster[selection])

    def remove_from_team(self, selection):
        self.members.pop(selection)
