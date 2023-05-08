from src.engine.init_engine import eng


class GameStateDumpers:
    @classmethod
    def guild_to_dict(cls) -> dict:
        state = eng.game_state.guild
        guild = {}

        guild["name"] = state.name
        guild["xp"] = state.xp
        guild["funds"] = state.funds
        guild["roster_limit"] = state.roster_limit
        guild["roster"] = [cls.entity_to_dict(entity) for entity in state.roster]
        guild["roster_scalar"] = state.roster_scalar
        guild["team"] = cls.team_to_dict(state.team)

        return guild

    @classmethod
    def entity_to_dict(cls, entity):
        return {
            "entity_id": entity.entity_id,
            "name": entity.name._asdict(),
            "cost": entity.cost,
            "fighter": cls.fighter_to_dict(entity.fighter),
            "inventory": entity.inventory.to_dict(),
            "species": entity.species,
        }

    @classmethod
    def team_to_dict(cls, team) -> dict:
        team_as_dict = {}

        team_as_dict["name"] = team.name
        team_as_dict["members"] = [
            cls.entity_to_dict(member) for member in team.members
        ]

        return team_as_dict

    @classmethod
    def fighter_to_dict(cls, fighter) -> dict:
        return {
            "role": fighter.role.name,
            "health": cls.health_pool_to_dict(fighter.health),
            "stats": fighter.stats._asdict(),
            "action_points": cls.action_points_to_dict(fighter.action_points),
            "equipment": cls.equipment_to_dict(fighter.equipment),
            "caster": cls.caster_to_dict(fighter.caster) if fighter.caster else None,
        }

    @classmethod
    def action_points_to_dict(cls, action_points) -> dict:
        return {"per_turn": action_points.per_turn}

    @classmethod
    def caster_to_dict(cls, caster):
        return {"mp_pool": cls.mp_pool_to_dict(caster.mp_pool)}

    @classmethod
    def mp_pool_to_dict(cls, mp_pool):
        return {"max": mp_pool.max, "current": mp_pool.current}

    @classmethod
    def health_pool_to_dict(cls, fighter_health_pool):
        return {
            "max": fighter_health_pool.max_hp,
            "current": fighter_health_pool.current,
            "bonus": fighter_health_pool.bonus,
        }

    @classmethod
    def equipment_to_dict(cls, equipment) -> dict:
        return {
            "weapon": cls.equippable_to_dict(equipment.weapon)
            if equipment.weapon
            else None,
            "helmet": cls.equippable_to_dict(equipment.helmet)
            if equipment.helmet
            else None,
            "body": cls.equippable_to_dict(equipment.body) if equipment.body else None,
        }

    @classmethod
    def equippable_to_dict(cls, equippable) -> dict:
        return {
            "config": cls.equippable_config_to_dict(equippable._config),
        }

    @classmethod
    def equippable_config_to_dict(cls, equippable_config):
        return {
            "name": equippable_config.name,
            "slot": equippable_config.slot,
            "attack_verb": equippable_config.attack_verb,
            "range": equippable_config.range,
            "attacks": equippable_config.attacks,
            "spells": equippable_config.spells,
            "affixes": [
                cls.stat_affix_to_dict(affix) for affix in equippable_config.affixes
            ]
            if equippable_config.affixes
            else [],
        }

    @classmethod
    def stat_affix_to_dict(cls, stat_affix):
        return {
            "name": stat_affix.name,
            "modifier": cls.modifier_to_dict(stat_affix.modifier),
        }

    @classmethod
    def modifier_to_dict(cls, modifier) -> dict:
        return {
            "stat_class": modifier._stat_class.name,
            "percent": modifier.percent._asdict(),
            "base": modifier.base._asdict(),
        }
