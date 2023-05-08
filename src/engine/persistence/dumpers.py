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
        team_as_dict["members"] = [cls.entity_to_dict(member) for member in team.members]

        return team_as_dict
    
    @classmethod
    def fighter_to_dict(cls, fighter) -> dict:
        return {
            "role": fighter.role.name,
            "health": fighter.health.to_dict(),
            "stats": fighter.stats._asdict(),
            "action_points": fighter.action_points.to_dict(),
            "equipment": fighter.equipment.to_dict(),
            "caster": fighter.caster.to_dict() if fighter.caster else None,
        }