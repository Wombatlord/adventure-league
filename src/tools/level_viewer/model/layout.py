from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable

import arcade

from src.gui.biome_textures import Biome, BiomeName
from src.world.level.room_layouts import TerrainNode
from src.world.node import Node


@dataclass
class Block:
    node: Node
    biome: Biome
    terrain_node: TerrainNode

    @property
    def texture(self) -> arcade.Texture:
        return self.biome.choose_tile_texture(self.terrain_node.tile_type)

    def with_biome(self, biome: Biome) -> Block:
        self.biome = biome
        return self


def from_terrain_nodes(tn: Iterable[TerrainNode]) -> list[Block]:
    biome_name = random.choice(BiomeName.all_biomes())
    return [Block(t.node, biome_name, t) for t in tn]


LayoutFactory = Callable[[tuple[int, int]], tuple["TerrainNode"]]
BlockFactory = Callable[[], list[Block]]
_viewable_layouts: dict[str, BlockFactory] = {}


def register_layout(layout_factory: LayoutFactory) -> LayoutFactory:
    global _viewable_layouts
    _viewable_layouts[layout_factory.__name__] = lambda dims: from_terrain_nodes(
        layout_factory(dims)
    )

    return layout_factory


def get_registered_layouts() -> dict[str, BlockFactory]:
    global _viewable_layouts
    return {**_viewable_layouts}
