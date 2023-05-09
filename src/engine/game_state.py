from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.engine.engine import Engine

from random import randint

from src.config.constants import guild_names
from src.engine.guild import Guild, Team
from src.engine.mission_board import MissionBoard
from src.entities.ai.ai import CombatAISubscriber
from src.entities.combat.fighter_factory import RecruitmentPool
from src.entities.entity import Entity
from src.systems.collision_avoidance import SpaceOccupancyHandler
from src.world.level.dungeon import Dungeon


class GameState:
    _guild: Optional[Guild] = None
    team: Optional[Team] = None
    entity_pool: Optional[RecruitmentPool] = None
    dungeon: Optional[Dungeon] = None
    mission_board: Optional[MissionBoard] = None

    def __init__(self, eng: Engine):
        mission_board = MissionBoard(size=3)
        mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
        self.set_mission_board(mission_board)
        self.occupancy_handler = SpaceOccupancyHandler(eng)
        self.combat_ai_handler = CombatAISubscriber(eng)

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

    @property
    def guild(self) -> Guild:
        return self._guild

    @guild.setter
    def guild(self, value: Guild):
        self._guild = value
        self.team = value.team

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

    def entities(self) -> list[Entity]:
        return self.entity_pool.pool + self.guild.roster


class AwardSpoilsHandler:
    def __init__(self, state: GameState):
        self.state = state

    def handle(self, event):
        """
        code etc
        """
        dungeon = event.get("team triumphant", {}).get("dungeon")
        if dungeon is None:
            return
        dungeon.cleared = True
        self.state.guild.claim_rewards(dungeon)
