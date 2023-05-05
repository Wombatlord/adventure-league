from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.action.actions import ActionMeta
    from src.entities.combat.fighter import Fighter
    from src.entities.combat.weapon_attacks import WeaponAttackMeta
    from src.entities.magic.spells import SpellMeta


class MetaCompendium:
    all_actions: dict[str, ActionMeta] = {}
    all_spells: dict[str, SpellMeta] = {}
    all_attacks: dict[str:WeaponAttackMeta] = {}

    @classmethod
    def all_registered_spells(cls) -> dict[str, SpellMeta]:
        return {name: spell for name, spell in cls.all_spells.items()}

    @classmethod
    def all_registered_attacks(cls) -> dict[str, WeaponAttackMeta]:
        return {name: attack for name, attack in cls.all_attacks.items()}

    @classmethod
    def all_actions_available_to(cls, fighter: Fighter) -> dict[str, ActionMeta]:
        action_dict = {
            name: action
            for name, action in cls.all_actions.items()
            if fighter.does(action)
        }

        def order_by_menu_pos(d: dict):
            return d[1].menu_pos

        ordered = dict(sorted(action_dict.items(), key=order_by_menu_pos))
        return ordered
