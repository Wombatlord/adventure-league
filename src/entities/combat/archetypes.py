import random
from enum import Enum


class FighterArchetype(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    CASTER = "caster"

    @classmethod
    def random_archetype(cls):
        return random.choice([*cls])
