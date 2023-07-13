from typing import Any, Generator, NamedTuple, Optional, Self, Sequence
from uuid import uuid4

from src.engine.events_enum import Events
from src.entities.ai.ai import AiInterface
from src.entities.combat.fighter import Fighter
from src.entities.item.inventory import Inventory
from src.entities.item.inventory_item import InventoryItem
from src.entities.properties.locatable import Locatable
from src.entities.sprite_assignment import Species, attach_sprites
from src.entities.sprites import AnimatedSpriteAttribute
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class Name(NamedTuple):
    first_name: str = None
    title: Optional[str] = None
    last_name: Optional[str] = None

    def __str__(self) -> str:
        return " ".join(filter(lambda x: (x is not None), self)).capitalize()

    @property
    def name_and_title(self) -> str:
        if self.has_title():
            return f"{self.first_name.capitalize()} {self.title}"
        else:
            return f"{self.first_name.capitalize()}"

    def has_title(self) -> bool:
        return self.title is not None


class Entity:
    entity_sprite: AnimatedSpriteAttribute | None
    fighter: Fighter | None
    inventory: Inventory | None
    ai: AiInterface | None

    def to_dict(self):
        return {
            "entity_id": self.entity_id,
            "name": self.name._asdict(),
            "cost": self.cost,
            "fighter": self.fighter.to_dict(),
            "inventory": self.inventory.to_dict(),
            "species": self.species,
        }

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
        self.entity_id = uuid4().hex.upper()
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

    @classmethod
    def get_by_id(cls, id: str, collection: Sequence[Self | Fighter]):
        for entity in collection:
            if isinstance(entity, Fighter):
                entity = entity.owner

            if entity.entity_id == id:
                return entity

    def with_inventory_capacity(self, capacity: int) -> Self:
        self.inventory = Inventory(owner=self, capacity=capacity)
        return self

    def set_entity_sprite(self, sprite: AnimatedSpriteAttribute):
        self.entity_sprite = sprite
        if self.entity_sprite:
            self.entity_sprite.owner = self

    def make_locatable(self, space: PathingSpace, spawn_point: Node):
        self.locatable = Locatable(
            owner=self,
            location=spawn_point,
            speed=self.fighter.stats.speed,
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
                Events.ENTITY_DATA: {
                    "health": self.fighter.health.current if self.fighter else None,
                    "name": self.name.name_and_title,
                    Events.RETREAT: self.fighter.retreating,
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
