from unittest import TestCase

from src.engine.guild import Guild
from src.engine.persistence.dumpers import GameStateDumpers
from src.engine.persistence.loaders import GameStateLoaders
from src.tests.fixtures import GuildFactory
from src.utils.deep_copy import copy


class SerialisationTest(TestCase):
    _is_set_up = False
    guild = None
    guild_dict = None
    guild_dict_cpy = None
    loaded_guild = None
    reserialised_guild = None
    
    def setup(self):
        if self._is_set_up:
            return
        self.guild = GuildFactory.make_guild()
        self.guild_dict = GameStateDumpers.guild_to_dict(self.guild)
        self.guild_dict_cpy = copy(self.guild_dict)
        self.loaded_guild = GameStateLoaders.guild_from_dict(self.guild_dict_cpy)
        self.reserialised_guild = GameStateDumpers.guild_to_dict(self.loaded_guild)
        self._is_set_up = True

    def test_guild_is_unchanged_after_serialisation_and_rehydration(self):
        # Arrange/Action
        self.setup()

        # Assert
        original_team = self.guild.team
        rehydrated_team = self.loaded_guild.team
        original_member_names = [member.name for member in original_team.members]
        rehydrated_member_names = [member.name for member in rehydrated_team.members]

        for name in original_member_names:
            assert name in rehydrated_member_names, f"Original team member name {name} was missing from the rehydrated team member names {rehydrated_member_names=}"
        