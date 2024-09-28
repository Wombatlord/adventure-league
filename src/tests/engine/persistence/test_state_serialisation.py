from unittest import TestCase

from src.engine.persistence.dumpers import GameStateDumpers
from src.engine.persistence.game_state_repository import (Format,
                                                          GuildRepository)
from src.engine.persistence.loaders import GameStateLoaders
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.modifiable_stats import Modifier
from src.entities.combat.stats import StatAffix
from src.entities.entity import Entity
from src.entities.gear.equippable_item import (EquippableItem,
                                               EquippableItemConfig)
from src.entities.gear.gear import Gear
from src.tests.fixtures import GuildFactory
from src.utils.deep_copy import copy


class SerialisationTest(TestCase):
    _is_set_up = False
    guild = None
    guild_dict = None
    guild_dict_cpy = None
    loaded_guild = None
    reserialised_guild = None
    formats = (Format.PICKLE, Format.YAML)

    def setup(self, force=False, create_save_file=True):
        if self._is_set_up and not force:
            return
        self.guild = GuildFactory.make_guild()
        # this is where to put stuff in

        self.guild_dict = GameStateDumpers.guild_to_dict(self.guild)
        self.guild_dict_cpy = copy(self.guild_dict)

        if create_save_file:
            GuildRepository.save(
                slot=0, guild_to_serialise=self.guild, fmts=self.formats, testing=True
            )
        # that you want to see reappear here
        self.loaded_guild = GameStateLoaders.guild_from_dict(self.guild_dict_cpy)

        self.reserialised_guild = GameStateDumpers.guild_to_dict(self.loaded_guild)
        self._is_set_up = True

    def test_rehydrated_fighter_in_roster_has_properly_rehydrated_equipment(self):
        # Arrange / Action
        self.setup(force=True)

        original_roster = self.guild.roster
        rehydrated_roster = self.loaded_guild.roster
        original_equipment: Gear = original_roster[0].fighter.gear
        rehydrated_equipment: Gear = rehydrated_roster[0].fighter.gear

        original_weapon_affixes = [
            affix for affix in original_equipment.weapon._fighter_affixes
        ]
        rehydrated_weapon_affixes = [
            affix for affix in rehydrated_equipment.weapon._fighter_affixes
        ]

        # Assert
        for affix in original_weapon_affixes:
            assert (
                affix in rehydrated_weapon_affixes
            ), f"Original affix {affix} was not found in Rehydrated Affixes: {rehydrated_weapon_affixes}"
            assert isinstance(
                affix, StatAffix
            ), f"Affix is not of Type StatAffix: {affix=}"
            assert isinstance(
                affix.modifier, Modifier
            ), f"Affix Modifier is not of Type Modifier: {affix.modifier}"

        assert isinstance(
            rehydrated_equipment.weapon, EquippableItem
        ), f"Equippable is wrong type. Expected: Equippable, Got: {rehydrated_equipment.weapon}"
        assert isinstance(
            rehydrated_equipment.weapon._config, EquippableItemConfig
        ), f"EquippableConfig is wrong type. Expected: EquippableConfig, Got: {rehydrated_equipment.weapon._config}"
        assert isinstance(
            rehydrated_equipment.helmet, EquippableItem
        ), f"Equippable is wrong type. Expected: Equippable, Got: {rehydrated_equipment.helmet}"
        assert isinstance(
            rehydrated_equipment.helmet._config, EquippableItemConfig
        ), f"EquippableConfig is wrong type. Expected: EquippableConfig, Got: {rehydrated_equipment.helmet._config}"
        assert isinstance(
            rehydrated_equipment.body, EquippableItem
        ), f"Equippable is wrong type. Expected: Equippable, Got: {rehydrated_equipment.body}"
        assert isinstance(
            rehydrated_equipment.body._config, EquippableItemConfig
        ), f"EquippableConfig is wrong type. Expected: EquippableConfig, Got: {rehydrated_equipment.body._config}"

    def test_team_member_names_are_unchanged_after_serialisation_and_rehydration(self):
        # Arrange/Action
        self.setup(force=True)

        original_team = self.guild.team
        rehydrated_team = self.loaded_guild.team
        original_member_names = [member.name for member in original_team.members]
        rehydrated_member_names = [member.name for member in rehydrated_team.members]

        # Assert
        for name in original_member_names:
            assert (
                name in rehydrated_member_names
            ), f"Original team member name {name} was missing from the rehydrated team member names {rehydrated_member_names=}"

    def test_entity_ids_are_unchanged_after_serialisation_and_rehydration(self):
        # Arrange / Action
        self.setup(force=True)

        original_entities = self.guild.roster + self.guild.team.members
        rehydrated_entities = self.loaded_guild.roster + self.loaded_guild.team.members

        original_ids = [entity.entity_id for entity in original_entities]
        rehydrated_ids = [entity.entity_id for entity in rehydrated_entities]

        # Assert
        for entity_id in original_ids:
            assert (
                entity_id in rehydrated_ids
            ), f"Entity ID not found in rehydrated ids. ID: {entity_id}, Rehydrated_IDs: {rehydrated_ids}"

    def test_current_health_and_mp_values_are_consistent_with_originals_after_rehydration(
        self,
    ):
        # Arrange / Action
        self.setup(force=True)

        original_entities = self.guild.roster + self.guild.team.members
        rehydrated_entities = self.loaded_guild.roster + self.loaded_guild.team.members

        for entity in original_entities:
            original_entity = Entity.get_by_id(entity.entity_id, original_entities)
            rehydrated_entity = Entity.get_by_id(entity.entity_id, rehydrated_entities)

            # Assert
            assert (
                original_entity.fighter.health.current
                == rehydrated_entity.fighter.health.current
            ), f"Current Health values different after rehydration. Expected {original_entity.fighter.health.current=}, Got: {rehydrated_entity.fighter.health.current}"

            if original_entity.fighter.caster:
                assert (
                    original_entity.fighter.caster.mp_pool.current
                    == rehydrated_entity.fighter.caster.mp_pool.current
                ), f"Current MP values different after rehydration. Expected {original_entity.fighter.caster.mp_pool.current=}, Got: {rehydrated_entity.fighter.caster.mp_pool.current}"

    def test_attack_and_spell_are_consistent_and_caches_are_filled_after_rehydration(
        self,
    ):
        # Arrange / Action
        self.setup(force=True)

        original_entities = self.guild.roster + self.guild.team.members
        rehydrated_entities = self.loaded_guild.roster + self.loaded_guild.team.members

        for entity in original_entities:
            original_entity = Entity.get_by_id(entity.entity_id, original_entities)
            rehydrated_entity = Entity.get_by_id(entity.entity_id, rehydrated_entities)
            original_entity_attacks = original_entity.fighter.gear.weapon._attacks
            rehydrated_entity_attacks = rehydrated_entity.fighter.gear.weapon._attacks
            rehydrated_entity_attack_cache = (
                rehydrated_entity.fighter.gear.weapon._available_attacks_cache
            )
            original_entity_spells = original_entity.fighter.gear.weapon._spells
            rehydrated_entity_spells = rehydrated_entity.fighter.gear.weapon._spells
            rehydrated_entity_spell_cache = (
                rehydrated_entity.fighter.gear.weapon._available_spells_cache
            )

            # Assert
            assert (
                original_entity_attacks == rehydrated_entity_attacks
            ), f"Attacks not consistent. Entity_A: {original_entity_attacks=}, Entity_B: {rehydrated_entity_attacks=}"
            assert (
                rehydrated_entity_attack_cache != []
            ), f"Weapon attacks cache is empty but should not be."

            if original_entity.fighter.caster:
                assert (
                    original_entity_spells == rehydrated_entity_spells
                ), f"Attacks not consistent. Entity_A: {original_entity_spells=}, Entity_B: {rehydrated_entity_spells=}"
                assert (
                    rehydrated_entity_spell_cache != []
                ), f"Spells cache is empty but should not be."

    def test_fighter_base_stats_and_modifiable_stats_are_consistent_after_rehydration(
        self,
    ):
        # Arrange / Action
        self.setup(force=True)

        original_entities = self.guild.roster + self.guild.team.members
        rehydrated_entities = self.loaded_guild.roster + self.loaded_guild.team.members

        for entity in original_entities:
            original_entity = Entity.get_by_id(entity.entity_id, original_entities)
            rehydrated_entity = Entity.get_by_id(entity.entity_id, rehydrated_entities)
            original_entity_stats = original_entity.fighter.modifiable_stats.current
            rehydrated_entity_stats = rehydrated_entity.fighter.modifiable_stats.current

            # Assert
            for i, stat in enumerate(original_entity.fighter.stats):
                assert (
                    stat == rehydrated_entity.fighter.stats[i]
                ), f"Base stats are not equivalent, Entity_A: {stat=}, Entity_B: {rehydrated_entity.fighter.stats[i]}"

            assert (
                original_entity_stats.defence == rehydrated_entity_stats.defence
            ), f"Modifiable Stat is not equal, Entity_A: {original_entity_stats.defence=}, Entity_B: {rehydrated_entity_stats.defence=}"
            assert (
                original_entity_stats.power == rehydrated_entity_stats.power
            ), f"Modifiable Stat is not equal, Entity_A: {original_entity_stats.power=}, Entity_B: {rehydrated_entity_stats.power=}"
            assert (
                original_entity_stats.speed == rehydrated_entity_stats.speed
            ), f"Modifiable Stat is not equal, Entity_A: {original_entity_stats.speed=}, Entity_B: {rehydrated_entity_stats.speed=}"
