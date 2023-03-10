from typing import Optional
from random import randint

from src.entities.guild import Guild, Team
from src.entities.fighter_factory import EntityPool
from src.entities.dungeon import Dungeon
from src.entities.mission_board import MissionBoard
from src.config.constants import guild_names


class GameState:
    guild: Optional[Guild] = None
    team: Optional[Team] = None
    entity_pool: Optional[EntityPool] = None
    dungeon: Optional[Dungeon] = None
    mission_board: Optional[MissionBoard] = None

    def setup(self):
        self.set_guild(
            Guild(
                name=guild_names[randint(0, len(guild_names) - 1)],
                xp=4000,
                funds=100,
                roster=[],
            )
        )

    def get_guild(self):
        return self.guild

    def get_team(self):
        return self.team

    def get_entity_pool(self):
        return self.entity_pool

    def get_dungeon(self):
        return self.dungeon

    def get_mission_board(self):
        return self.mission_board

    def set_guild(self, guild):
        self.guild = guild

    def set_team(self):
        self.team = self.guild.team

    def set_entity_pool(self, pool):
        self.entity_pool = pool

    def set_dungeon(self, dungeon):
        self.dungeon = dungeon

    def set_mission_board(self, board):
        self.mission_board = board