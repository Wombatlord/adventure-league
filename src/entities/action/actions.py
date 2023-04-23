from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter
    from src.world.node import Node
    from src.entities.item.items import Consumable

from typing import Any, Generator

from src.entities.combat.attack_types import attack

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


class ActionCompendium:
    all_actions: dict[str, ActionMeta] = {}

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> dict[str, ActionMeta]:
        try:
            return {
                name: action
                for name, action in cls.all_actions.items()
                if fighter.does(action)
            }
        except Exception as e:
            breakpoint()


class ActionMeta(type):
    name: str

    def __new__(cls, *args, **kwargs):
        action_class = super().__new__(cls, *args, **kwargs)
        ActionCompendium.all_actions[action_class.name] = action_class

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


class AttackAction(BaseAction, metaclass=ActionMeta):
    name = "attack"

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(cls, fighter: Fighter, target: Fighter) -> Generator[Event]:
        fighter.action_points.deduct_cost(cls.cost(fighter))
        yield attack(fighter=fighter, target=target.owner)

    @classmethod
    def details(cls, fighter: Fighter, target: Fighter) -> dict:
        return {
            **ActionMeta.details(cls, fighter),
            "on_confirm": lambda: fighter.ready_action(cls(fighter, target)),
            "subject": target,
            "label": f"{target.owner.name}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        return [
            cls.details(fighter, occupant.fighter)
            for occupant in fighter.locatable.entities_in_range(
                room=fighter.encounter_context.get(),
                max_range=fighter.max_range,
                entity_filter=lambda e: fighter.is_enemy_of(e.fighter),
            )
        ]

    def __init__(self, fighter: Fighter, target: Fighter) -> None:
        self.fighter = fighter
        self.target = target

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.target)


class MoveAction(BaseAction, metaclass=ActionMeta):
    name = "move"

    @classmethod
    def cost(cls, fighter: Fighter, destination: Node | None = None) -> int:
        # by default, the move is trivial
        if destination is None:
            destination = fighter.locatable.location

        locatable = fighter.locatable

        # not moving costs nothing
        if destination == locatable.location:
            return 0

        distance = len(locatable.path_to_destination(destination)[1:])

        # We want this to be 0 if distance <= speed
        distance_cost = (distance - 1) // locatable.speed

        base_cost = 1

        total_cost = base_cost + distance_cost

        return total_cost

    @classmethod
    def execute(
        cls, fighter: Fighter, destination: Node
    ) -> Generator[Event, None, None]:
        cost = cls.cost(fighter, destination)
        fighter.action_points.deduct_cost(cost)
        path = fighter.locatable.path_to_destination(destination)
        yield from fighter.locatable.traverse(path)

    @classmethod
    def details(cls, fighter: Fighter, destination: Node) -> dict:
        path = fighter.locatable.path_to_destination(destination)
        return {
            **ActionMeta.details(cls, fighter, destination),
            "subject": path,
            "on_confirm": lambda: fighter.ready_action(cls(fighter, destination)),
            "label": f"{path[-1]}",
        }

    @classmethod
    def all_available_to(cls, fighter: Fighter) -> list[dict]:
        available = []
        for path in fighter.locatable.available_moves(speed=fighter.stats.speed):
            available.append(cls.details(fighter, destination=path[-1]))

        return available

    def __init__(self, fighter: Fighter, destination: Node) -> None:
        self.fighter = fighter
        self.destination = destination

    def __call__(self) -> Generator[Event]:
        yield from self.execute(self.fighter, self.destination)


class ConsumeItemAction(BaseAction, metaclass=ActionMeta):
    name = "use item"

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

    @classmethod
    def cost(cls, fighter: Fighter) -> int:
        return fighter.action_points.current

    @classmethod
    def execute(cls, fighter: Fighter, *args):
        fighter.action_points.deduct_cost(cls.cost(fighter))
        yield {"message": f"{fighter.owner.name} whistles a tune"}

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
