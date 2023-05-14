import random
from typing import Callable

from src.entities.combat.archetypes import FighterArchetype
from src.entities.gear.armour import breastplate, helmet
from src.entities.gear.equippable_item import EquippableItem
from src.entities.gear.weapons import bow, spellbook, sword


def default_equippable_item_factory(
    gearset_config: dict | None = None,
) -> Callable[[FighterArchetype], dict[str, EquippableItem]]:
    gearset_config = gearset_config or {
        "_weapon": {"melee": (sword,), "ranged": (bow,), "caster": (spellbook,)},
        "_helmet": {"melee": (helmet,), "ranged": (helmet,), "caster": (helmet,)},
        "_body": {
            "melee": (breastplate,),
            "ranged": (breastplate,),
            "caster": (breastplate,),
        },
    }

    def factory(role: FighterArchetype) -> dict[str, EquippableItem]:
        weapons = gearset_config.get("_weapon", {})
        helmets = gearset_config.get("_helmet", {})
        bodies = gearset_config.get("_body", {})

        return {
            "_weapon": EquippableItem(
                owner=None, config=random.choice(weapons[role.value])
            ),
            "_helmet": EquippableItem(
                owner=None, config=random.choice(helmets[role.value])
            ),
            "_body": EquippableItem(
                owner=None, config=random.choice(bodies[role.value])
            ),
        }

    return factory
