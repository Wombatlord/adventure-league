import random
from enum import Enum


class FighterArchetype(Enum):
    MELEE = "melee"
    RANGED = "ranged"
    CASTER = "caster"

    @classmethod
    def random_archetype(cls):
        return random.choice([*cls])

    def role_options(self):
        match self:
            case self.MELEE:
                return []
            
            case self.RANGED:
                return []
            
            case self.CASTER:
                return []
            
            case _:
                return []