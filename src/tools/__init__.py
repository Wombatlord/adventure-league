import sys
from typing import NamedTuple

from src.textures import flat_sprite_maps, height_mapped_block
from src.utils.proc_gen.data_textures.texture_composer import (
    AssetMaterialiser, render_data_texture_to_terminal)


class ToolNames(NamedTuple):
    viewer = "level_viewer"
    height_map = "generate_heightmap"
    char_normals = "generate_character_normals"
    char_heights = "generate_character_heights"
    tile_normals = "generate_tile_normals"
    tile_heights = "generate_tile_heights"
    materialise = "materialise"
    data_texture = "data_texture"


def run_level_viewer():
    from src.tools import level_viewer

    level_viewer.start()


registered_tools = {
    ToolNames.height_map: height_mapped_block.generate,
    ToolNames.char_normals: flat_sprite_maps.character_normals,
    ToolNames.char_heights: flat_sprite_maps.character_height_maps,
    ToolNames.tile_normals: flat_sprite_maps.tile_normals,
    ToolNames.tile_heights: flat_sprite_maps.tile_heights,
    ToolNames.viewer: run_level_viewer,
    ToolNames.materialise: AssetMaterialiser.materialise,
    ToolNames.data_texture: render_data_texture_to_terminal,
}
