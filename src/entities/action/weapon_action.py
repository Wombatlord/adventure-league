from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.world.node import Node

from typing import Any, Generator

from src.entities.action.actions import ActionMeta, BaseAction
from src.entities.combat.weapon_attacks import WeaponAttackMeta

Event = dict[str, Any]


class WeaponAttackAction(BaseAction, metaclass=ActionMeta):
    name = "weapon attack"
    menu_pos = 0

    @classmethod
    def cost(cls, fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(
        cls, fighter: Fighter, target: Fighter, attack: WeaponAttackMeta
    ) -> Generator[Event]:
        if fighter.action_points.current >= attack.ap_cost:
            fighter.action_points.deduct_cost(cls.cost(fighter))
            yield attack.attack(target=target.owner)

        else:
            yield {"message": f"Not enough AP for {attack.name}"}

    @classmethod
    def details(cls, fighter: Fighter, attack: WeaponAttackMeta) -> dict:
        on_confirm = lambda target: fighter.ready_action(cls(fighter, target, attack))

        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": on_confirm,
            "subject": attack,
            "label": f"{attack.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [
            cls.details(fighter, attack)
            for attack in fighter.equipment.weapon.available_attacks
        ]

    def __init__(
        self, fighter: Fighter, target: Fighter, attack: WeaponAttackMeta
    ) -> None:
        self.fighter = fighter
        self.target = target
        self.attack = attack

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.target, self.attack)
