from typing import Any, NamedTuple, Optional, Self

from src.entities.ai.ai import AiInterface
from src.entities.item.inventory import Inventory, InventoryItem
from src.entities.properties.locatable import Locatable
from src.entities.sprites import EntitySprite
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


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


class Species:
    GOBLIN = "goblin"
    SLIME = "slime"
    HUMAN = "human"


class Entity:
    entity_sprite: EntitySprite | None
    inventory: Inventory | None
    ai: AiInterface | None

    def __init__(
        self,
        sprite=None,
        name: Name = None,
        cost: int = None,
        fighter=None,
        inventory=None,
        item: InventoryItem | None = None,
        is_dead: bool = False,
        species: str = Species.HUMAN,
        ai: AiInterface | None = None,
    ) -> None:
        self.name = name
        self.cost = cost
        self.inventory = inventory
        self.item = item
        self.is_dead = is_dead
        self.on_death_hooks = []
        self.species = species
        # Entities with a fighter component can engage in combat.
        self.fighter = fighter
        self.ai = ai
        if self.fighter:
            self.fighter.owner = self

        self.entity_sprite = None
        self.set_entity_sprite(sprite)

        self.locatable = None

    def with_inventory_capacity(self, capacity: int) -> Self:
        self.inventory = Inventory(owner=self, capacity=capacity)
        return self

    def set_entity_sprite(self, sprite: EntitySprite):
        self.entity_sprite = sprite
        if self.entity_sprite:
            self.entity_sprite.owner = self

    def make_locatable(self, space: PathingSpace, spawn_point: Node):
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
                    "species": self.species,
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
