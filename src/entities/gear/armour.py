from src.entities.combat.stats import (
    EquippableItemStats,
    percent_crit_increase,
    percent_power_increase,
    raw_defence_increase,
    raw_power_increase,
)
from src.entities.gear.equippable_item import EquippableItemConfig

helmet = EquippableItemConfig(
    name="helmet",
    slot="_helmet",
    fighter_affixes=[percent_power_increase],
    stats=EquippableItemStats(
        crit=0,
        block=0,
        evasion=0,
    ),
)

breastplate = EquippableItemConfig(
    name="breastplate",
    slot="_body",
    fighter_affixes=[raw_power_increase, raw_defence_increase],
    equippable_item_affixes=[percent_crit_increase],
    stats=EquippableItemStats(
        crit=0,
        block=0,
        evasion=0.15,
    ),
)
