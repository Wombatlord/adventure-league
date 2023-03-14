from __future__ import annotations

from random import randint
from typing import Optional

from src.config.constants import team_names
from src.entities.entity import Entity
from src.entities.loot import Loot


class Guild:
    def __init__(
        self,
        name: str = None,
        funds: int = 0,
        roster_limit: int = None,
        roster: list[Entity] = None,
        xp: int = 0,
    ) -> None:
        self.name = name
        self.funds = funds
        self.roster_limit = roster_limit
        self.roster = roster
        self.roster_scalar = 1.5
        self.xp = xp

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

    def claim_rewards(self, rewards: Loot):
        self.funds += rewards.claim_gp()
        self.xp += rewards.claim_xp()

    @property
    def level(self) -> int:
        return self.xp // 1000


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

    def assign_to_team(self, entity: Entity):
        # Clear out any hooks registered from previous assignment
        entity.on_death_hooks = []

        entity.on_death_hooks.append(self.remove_dead_member)
        entity.fighter.on_retreat_hooks.append(self.move_fighter_to_roster)

        entity.fighter.retreating = False
        self.members.append(entity)

    def move_fighter_to_roster(self, entity):
        try:
            self.owner.roster.append(self.members.pop(self.members.index(entity)))
        
        except ValueError:
            pass

    def remove_dead_member(self, entity):
        if entity in self.members:
            self.members.pop(self.members.index(entity))

        # In the case where an entity has been killed after initiating retreat
        # The entity must be removed from the roster rather than the team.
        if entity in self.owner.roster:
            self.owner.roster.pop(self.owner.roster.index(entity))
