from enum import Enum


class EventTopic(Enum):
    NEW_ENCOUNTER = "new encounter"
    DUNGEON = "dungeon context"
    COMBAT_START = "combat start"
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
    ROLL_ITEM_DROP = "roll item drop"


class EventFields(Enum):
    TEAM_XP = "guild xp"
    DUNGEON = "dungeon context"
    IN_MOTION = "in motion"
