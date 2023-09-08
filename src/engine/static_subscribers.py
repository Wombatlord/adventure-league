from src.engine.engine import Engine
from src.entities.ai import ai
from src.entities.item import equipment_rewards
from src.systems import collision_avoidance


def subscribe(eng: Engine):
    ai.subscribe(eng)
    collision_avoidance.subscribe(eng)
    equipment_rewards.subscribe(eng)
