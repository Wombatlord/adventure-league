from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.armory import Armory
from src.entities.combat.leveller import Leveller

if TYPE_CHECKING:
    from src.engine.guild import Guild, Team
    from src.entities.action.actions import ActionPoints
    from src.entities.combat.fighter import Fighter
    from src.entities.combat.modifiable_stats import Modifier
    from src.entities.combat.stats import HealthPool, StatAffix
    from src.entities.entity import Entity
    from src.entities.gear.equippable_item import (EquippableItem,
                                                   EquippableItemConfig)
    from src.entities.gear.gear import Gear
    from src.entities.magic.caster import Caster, MpPool


class GameStateDumpers:
    @classmethod
    def guild_to_dict(cls, guild: Guild) -> dict:
        guild_dict = {}

        guild_dict["name"] = guild.name
        guild_dict["xp"] = guild.xp
        guild_dict["funds"] = guild.funds
        guild_dict["roster_limit"] = guild.roster_limit
        guild_dict["roster"] = [cls.entity_to_dict(entity) for entity in guild.roster]
        guild_dict["roster_scalar"] = guild.roster_scalar
        guild_dict["team"] = cls.team_to_dict(guild.team)
        guild_dict["armory"] = cls.armory_to_dict(guild.armory)

        return guild_dict

    @classmethod
    def armory_to_dict(cls, armory: Armory) -> dict:
        return {
            "storage": [cls.equippable_item_to_dict(item) for item in armory.storage]
        }

    @classmethod
    def entity_to_dict(cls, entity: Entity) -> dict:
        return {
            "entity_id": entity.entity_id,
            "name": entity.name._asdict(),
            "cost": entity.cost,
            "fighter": cls.fighter_to_dict(entity.fighter),
            "inventory": entity.inventory.to_dict(),
            "species": entity.species,
        }

    @classmethod
    def team_to_dict(cls, team: Team) -> dict:
        team_as_dict = {}

        team_as_dict["name"] = team.name
        team_as_dict["members"] = [
            cls.entity_to_dict(member) for member in team.members
        ]

        return team_as_dict

    @classmethod
    def fighter_to_dict(cls, fighter: Fighter) -> dict:
        return {
            "role": fighter.role.name,
            "health": cls.health_pool_to_dict(fighter.health),
            "stats": fighter.stats._asdict(),
            "leveller": cls.leveller_to_dict(fighter.leveller),
            "action_points": cls.action_points_to_dict(fighter.action_points),
            "gear": cls.gear_to_dict(fighter.gear),
            "caster": cls.caster_to_dict(fighter.caster) if fighter.caster else None,
        }

    @classmethod
    def leveller_to_dict(cls, leveller: Leveller):
        return {
            "current_level": leveller.current_level,
            "current_xp": leveller.current_xp,
        }

    @classmethod
    def action_points_to_dict(cls, action_points: ActionPoints) -> dict:
        return {"per_turn": action_points.per_turn}

    @classmethod
    def caster_to_dict(cls, caster: Caster) -> dict:
        return {"mp_pool": cls.mp_pool_to_dict(caster.mp_pool)}

    @classmethod
    def mp_pool_to_dict(cls, mp_pool: MpPool) -> dict:
        return {"max": mp_pool.max, "current": mp_pool.current}

    @classmethod
    def health_pool_to_dict(cls, fighter_health_pool: HealthPool) -> dict:
        return {
            "max": fighter_health_pool.max_hp,
            "current": fighter_health_pool.current,
            "bonus": fighter_health_pool.bonus,
        }

    @classmethod
    def gear_to_dict(cls, gear: Gear) -> dict:
        return {
            "_weapon": cls.equippable_item_to_dict(gear.weapon)
            if gear.weapon
            else None,
            "_helmet": cls.equippable_item_to_dict(gear.helmet)
            if gear.helmet
            else None,
            "_body": cls.equippable_item_to_dict(gear.body) if gear.body else None,
            "base_equipped_stats": gear.base_equipped_stats._asdict(),
        }

    @classmethod
    def equippable_item_to_dict(cls, equippable: EquippableItem) -> dict:
        return {
            "config": cls.equippable_item_config_to_dict(
                equippable._config,
                equippable._fighter_affixes,
                equippable._equippable_item_affixes,
            ),
            "stats": equippable._stats._asdict(),
        }

    @classmethod
    def equippable_item_config_to_dict(
        cls,
        equippable_config: EquippableItemConfig,
        resolved_fighter_affixes,
        resolved_equippable_affixes,
    ) -> dict:
        return {
            "name": equippable_config.name,
            "slot": equippable_config.slot,
            "attack_verb": equippable_config.attack_verb,
            "range": equippable_config.range,
            "attacks": equippable_config.attacks,
            "spells": equippable_config.spells,
            "fighter_affixes": [
                cls.stat_affix_to_dict(affix) for affix in resolved_fighter_affixes
            ]
            if resolved_fighter_affixes
            else [],
            "equippable_item_affixes": [
                cls.stat_affix_to_dict(affix) for affix in resolved_equippable_affixes
            ]
            if resolved_equippable_affixes
            else [],
        }

    @classmethod
    def stat_affix_to_dict(cls, stat_affix: StatAffix) -> dict:
        return {
            "name": stat_affix.name,
            "modifier": cls.modifier_to_dict(stat_affix.modifier),
        }

    @classmethod
    def modifier_to_dict(cls, modifier: Modifier) -> dict:
        return {
            "stat_class": modifier._stat_class.name,
            "percent": modifier.percent._asdict(),
            "base": modifier.base._asdict(),
        }
