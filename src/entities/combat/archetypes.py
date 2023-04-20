import random
from enum import Enum


class FighterArchetype(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    CASTER = "caster"

    @classmethod
    def random_archetype(cls):
        selection = random.randint(0, 1)

        match selection:
            case 0:
                return cls.MELEE

            case 1:
                return cls.RANGED

            case 2:
                return cls.CASTER
