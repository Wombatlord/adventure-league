from enum import Enum


class Events(Enum):
    NEW_ENCOUNTER = "new encounter"
    DUNGEON = "dungeon context"
    DELAY = "delay"
    MESSAGE = "message"
    MOVE = "move"
    ATTACK = "attack"
    DYING = "dying"
    RETREAT = "retreat"
    VICTORY = "team triumphant"
    TEAM_XP = "guild xp"
    CLEANUP = "cleanup"
    ENTITY_DATA = "entity_data"
    HEALTH = "health"
    NAME = "name"
    SPECIES = "species"
