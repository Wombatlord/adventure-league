from __future__ import annotations

import random
from typing import TYPE_CHECKING, Generator, NamedTuple, Self

from src.gui.biome_textures import Biome, BiomeName, BiomeTextures

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.entities.entity import Entity
from src.world.level.room_layouts import TerrainNode, basic_room
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class RoomTexturer(NamedTuple):
    biome: BiomeName
    castle = BiomeTextures.castle()
    snow = BiomeTextures.snow()
    desert = BiomeTextures.desert()
    terrain_nodes: list[TerrainNode]

    def apply_biome_textures(self) -> Self:
        match self.biome:
            case BiomeName.CASTLE:
                self.castle_textures()

            case BiomeName.DESERT:
                self.desert_textures()

            case BiomeName.SNOW:
                self.snow_textures()

    def snow_textures(self):
        for terrain_node in self.terrain_nodes:
            if terrain_node.name == Biome.FLOOR:
                terrain_node.texture = random.choice(self.snow.floor_tiles)

            if terrain_node.name == Biome.WALL:
                terrain_node.texture = random.choice(self.snow.wall_tiles)

            if terrain_node.name == Biome.PILLAR:
                terrain_node.texture = random.choice(self.snow.pillar_tiles)

    def desert_textures(self):
        for terrain_node in self.terrain_nodes:
            if terrain_node.name == Biome.FLOOR:
                terrain_node.texture = random.choice(self.desert.floor_tiles)

            if terrain_node.name == Biome.WALL:
                terrain_node.texture = random.choice(self.desert.wall_tiles)

            if terrain_node.name == Biome.PILLAR:
                terrain_node.texture = random.choice(self.desert.pillar_tiles)

    def castle_textures(self):
        for terrain_node in self.terrain_nodes:
            if terrain_node.name == Biome.FLOOR:
                terrain_node.texture = random.choice(self.castle.floor_tiles)

            if terrain_node.name == Biome.WALL:
                terrain_node.texture = random.choice(self.castle.wall_tiles)

            if terrain_node.name == Biome.PILLAR:
                terrain_node.texture = random.choice(self.castle.pillar_tiles)


class Room:
    space: PathingSpace | None

    def __init__(
        self, biome: str = BiomeName.CASTLE, size: tuple[int, int] = (10, 10)
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
        self.space = PathingSpace.from_level_geometry(self.layout)
        return self

    def update_pathing_obstacles(self):
        """
        Used to synchronise the traversable locations with updated entity locations
        Returns:

        """
        exclusions = {occupant.locatable.location for occupant in self.occupants}
        self.space.exclusions = exclusions

    def add_entity(self, entity: Entity):
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
