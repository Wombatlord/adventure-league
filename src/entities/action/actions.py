from __future__ import annotations

from typing import TYPE_CHECKING, Self

from src.engine.events_enum import EventTopic
from src.entities.properties.meta_compendium import MetaCompendium

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.world.node import Node
    from src.entities.item.items import Consumable

from typing import Any, Generator

Event = dict[str, Any]


class ActionPoints:
    def __init__(self, per_turn=2):
        self.per_turn = per_turn
        self.current = self.per_turn

    def on_turn_start(self):
        self.current = self.per_turn

    def deduct_cost(self, cost: int) -> int:
        self.current -= abs(cost)
        return self.current


class ActionMeta(type):
    name: str

    def __new__(cls, *args, **kwargs):
        action_class = super().__new__(cls, *args, **kwargs)
        MetaCompendium.all_actions[action_class.name] = action_class

        return action_class

    def cost(cls, *args, **kwargs) -> int:
        raise NotImplementedError()

    def execute(cls, *args) -> Generator[Event]:
        raise NotImplementedError()

    def details(cls, fighter: Fighter, *args) -> dict:
        return {
            "name": cls.name,
            "actor": fighter,
            "cost": cls.cost(fighter, *args),
            "subject": None,
        }

    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        raise NotImplementedError()


class BaseAction:
    name = "BASE"

    def __init__(self, *args):
        raise NotImplementedError()

    def __call__(self, *args) -> Generator[Event]:
        raise NotImplementedError()


class MoveAction(BaseAction, metaclass=ActionMeta):
    name = "move"
    menu_pos = 2

    @classmethod
    def cost(
        cls, fighter: Fighter, destination: Node | None = None
    ) -> tuple[int, tuple[Node]]:
        # by default, the move is trivial
        if destination is None:
            destination = fighter.locatable.location

        locatable = fighter.locatable

        # not moving costs nothing
        if destination == locatable.location:
            return 0

        # If the player has selected a node beyond the end of the highlighted path,
        # Only calculate the cost of the part of the path that will actually be traversed.
        full_path = locatable.path_to_destination(destination)
        path = full_path[1:]
        if len(path) > locatable.speed:
            path = path[: locatable.speed]
        distance = len(path)

        # We want this to be 0 if distance <= speed
        distance_cost = (distance - 1) // locatable.speed

        base_cost = 1

        total_cost = base_cost + distance_cost

        return total_cost, full_path

    @classmethod
    def execute(
        cls, fighter: Fighter, destination: Node
    ) -> Generator[Event, None, None]:
        cost, path = cls.cost(fighter, destination)
        fighter.action_points.deduct_cost(cost)
        yield from fighter.locatable.traverse(path)

    @classmethod
    def details(cls, fighter: Fighter) -> dict:
        return {
            **ActionMeta.details(cls, fighter),
            "subject": fighter,
            "on_confirm": lambda destination: fighter.ready_action(
                cls(fighter, destination)
            ),
            "label": f"{fighter.owner.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [cls.details(fighter)]

    def __init__(self, fighter: Fighter, destination: Node) -> None:
        self.fighter = fighter
        self.destination = destination

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.destination)


class ConsumeItemAction(BaseAction, metaclass=ActionMeta):
    name = "use item"
    menu_pos = 3

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(cls, fighter: Fighter, consumable: Consumable) -> Generator[Event]:
        fighter.action_points.deduct_cost(cls.cost(fighter))
        yield from fighter.consume_item(consumable)

    @classmethod
    def details(cls, fighter: Fighter, consumable: Consumable) -> dict:
        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": lambda: fighter.ready_action(cls(fighter, consumable)),
            "subject": consumable,
            "label": f"{consumable.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [
            cls.details(fighter, consumable)
            for consumable in fighter.owner.inventory.consumables()
        ]

    def __init__(self, fighter: Fighter, consumable: Consumable) -> None:
        self.fighter = fighter
        self.consumable = consumable

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.consumable)


class EndTurnAction(BaseAction, metaclass=ActionMeta):
    name = "end turn"
    menu_pos = 500

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(cls, fighter: Fighter, *args):
        fighter.action_points.deduct_cost(cls.cost(fighter))
        yield {EventTopic.MESSAGE: f"{fighter.owner.name} whistles a tune"}

    @classmethod
    def details(cls, fighter: Fighter):
        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": lambda: fighter.ready_action(cls(fighter)),
            "label": "Confirm",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [cls.details(fighter)]

    def __init__(self, fighter: Fighter) -> None:
        self.fighter = fighter

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter)
