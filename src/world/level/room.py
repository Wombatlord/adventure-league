from __future__ import annotations

from typing import TYPE_CHECKING, Generator, NamedTuple, Self

from src.gui.biome_textures import BiomeName, biome_map

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.entities.entity import Entity
from src.world.level.room_layouts import Terrain, TerrainNode, basic_room
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class RoomTexturer(NamedTuple):
    biome_name: BiomeName
    terrain_nodes: list[TerrainNode]

    def apply_biome_textures(self) -> Self:
        biome_textures = biome_map[self.biome_name]
        for terrain_node in self.terrain_nodes:
            terrain_node.texture = biome_textures.choose_tile_texture(
                terrain_node.tile_type
            )


class Room:
    space: PathingSpace | None

    def __init__(
        self,
        size: tuple[int, int] = (10, 10),
        biome: str = BiomeName.CASTLE,
    ) -> None:
        self.layout = None
        self.space = None
        self.biome = biome
        self.room_texturer = None
        self.enemies: list[Entity] = []
        self.occupants: list[Entity] = []
        self._cleared = False
        self.entry_door = Node(x=0, y=5) if size[1] > 5 else Node(0, 0)

    def set_layout(self, layout: tuple[TerrainNode, ...]) -> Self:
        self.layout = layout
        self.room_texturer = RoomTexturer(self.biome, self.layout)
        self.space = PathingSpace.from_terrain(Terrain(self.layout))
        return self

    def update_pathing_obstacles(self):
        """
        Used to synchronise the traversable locations with updated entity locations
        Returns:

        """
        exclusions = {occupant.locatable.location for occupant in self.occupants}
        self.space.exclusions = exclusions

    def add_entity(self, entity: Entity):
        if self.layout is None:
            raise ValueError(
                "Cannot add entities to a room without a layout. Did you miss a call to set_layout()?"
            )

        mob_spawns = self.mob_spawns_points()
        if entity.fighter.is_enemy:
            spawn_point = next(mob_spawns)
        else:
            spawn_point = self.space.choose_next_unoccupied(self.entry_door)

        entity.make_locatable(self.space, spawn_point=spawn_point)
        self.occupants.append(entity)  # <- IMPORTANT:
        self.update_pathing_obstacles()  # <- don't change the order of these two!

        if entity.fighter.is_enemy:
            self.enemies.append(entity)

        entity.on_death_hooks.extend(
            [
                self.remove,
                Entity.flush_locatable,
            ]
        )
        entity.fighter.on_retreat_hooks.extend(
            [
                lambda f: self.remove(f.owner),
                lambda f: Entity.flush_locatable(f.owner),
            ]
        )

        fighter: Fighter = entity.fighter
        fighter.encounter_context.set(self)

    def include_party(self, party: list[Entity]) -> list[Entity]:
        for member in party:
            self.add_entity(member)
        return party

    def mob_spawns_points(self) -> Generator[Node, None, None]:
        while True:
            yield self.space.choose_random_node(
                excluding=self.space.exclusions,
            )

    def remove(self, entity: Entity):
        if hasattr(entity, "owner"):
            entity = entity.owner
        elif not isinstance(entity, Entity):
            raise TypeError(
                f"Can only remove Entities and owned components from the room, got {entity}",
            )
        if entity.fighter.is_enemy:
            self.enemies.pop(self.enemies.index(entity))
        self.occupants.pop(self.occupants.index(entity))

    @property
    def cleared(self):
        return self._cleared

    @cleared.setter
    def cleared(self, new_value):
        current_value = self.cleared

        if new_value != current_value:
            print("ROOM CLEAR!")
