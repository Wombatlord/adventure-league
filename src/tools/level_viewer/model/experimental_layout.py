from __future__ import annotations

from typing import Callable, TypeVar

from src.gui.biome_textures import Biome
from src.world.level.room_layouts import Terrain, TerrainNode
from src.world.node import Node

_LoadedType = TypeVar("_LoadedType", bound=object)

_LoadFunc = Callable[[dict], _LoadedType]
_Decorator = Callable[[_LoadFunc], _LoadFunc]

_loaders: dict[str, _LoadFunc] = {}


def loads(cls: _LoadedType) -> _Decorator:
    def _decorator(func: _LoadFunc) -> _LoadFunc:
        global _loaders
        _loaders[cls.__name__] = func
        return func

    return _decorator


class Voxel:
    node: Node
    voxel_type: int

    def __init__(self, x: int, y: int, z: int | float, object_type: int):
        self.node = Node(x, y, z)
        self.voxel_type = object_type

    def as_dict(self) -> dict:
        return {
            "__name__": self.__class__.__name__,
            "__dict__": {"node": [*self.node], "voxel_type": self.voxel_type},
        }


@loads(Voxel)
def voxel_loader(dict_: dict) -> Voxel:
    name = dict_.get("__name__")
    if not name:
        raise TypeError("Missing name")

    data = dict_.get("__data__", {})
    node = data.get("node")
    voxel_type = data.get("voxel_type")

    return Voxel(*node, voxel_type)


class Level:
    voxels: tuple[Voxel]

    def get_geometry(self) -> tuple[Node]:
        return tuple(v.node for v in self.voxels)

    def build_terrain(self, biome: Biome) -> Terrain:
        terrain_nodes = []
        for voxel in self.voxels:
            texture = biome.choose_tile_texture(voxel.voxel_type)
            terrain_node = TerrainNode(voxel.node, voxel.voxel_type)
            terrain_node.texture = texture

            terrain_nodes.append(terrain_node)

        return Terrain(terrain_nodes)
