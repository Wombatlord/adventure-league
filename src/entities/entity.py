from typing import Any, NamedTuple, Optional

from src.entities.locatable import Locatable
from src.entities.sprites import EntitySprite
from src.utils.pathing.grid_utils import Node, Space


class Name(NamedTuple):
    first_name: str = None
    title: Optional[str] = None
    last_name: Optional[str] = None

    def __str__(self) -> str:
        return " ".join(filter(lambda x: (x is not None), self))

    @property
    def name_and_title(self) -> str:
        if self.has_title():
            return f"{self.first_name.capitalize()} {self.title}"
        else:
            return f"{self.first_name.capitalize()}"

    def has_title(self) -> bool:
        return self.title is not None


class Entity:
    def __init__(
        self,
        sprite=None,
        name: Name = None,
        cost: int = None,
        fighter=None,
        inventory=None,
        item=None,
        is_dead: bool = False,
    ) -> None:
        self.name = name
        self.cost = cost
        self.inventory = inventory
        self.item = item
        self.is_dead = is_dead
        self.on_death_hooks = []

        # Entities with a fighter component can engage in combat.
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.entity_sprite: EntitySprite = sprite
        if self.entity_sprite:
            self.entity_sprite.owner = self

        self.locatable = None

    def make_locatable(self, space: Space, spawn_point: Node):
        self.locatable = Locatable(
            owner=self,
            location=spawn_point,
            speed=self.fighter.speed,
            space=space,
        )

    def flush_locatable(self) -> None:
        self.locatable = None

    def get_dict(self) -> dict:
        # returns a dict for serialisation of an entity.
        result = {}

        result["name"] = self.name
        result["cost"] = self.cost

        if self.fighter:
            result["fighter"] = self.fighter.get_dict()

        if self.inventory:
            result["inventory"] = self.inventory.get_dict()

        if self.item:
            result["item"] = self.item

        return result

    def annotate_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            **event,
            **{
                "entity_data": {
                    "health": self.fighter.hp if self.fighter else None,
                    "name": self.name.name_and_title,
                    "retreat": self.fighter.retreating,
                }
            },
        }

    def die(self):
        hooks = self.on_death_hooks
        while hooks and (hook := hooks.pop(0)):
            hook(self)

    def clear_hooks(self):
        self.on_death_hooks = []
        self.fighter.clear_hooks()
