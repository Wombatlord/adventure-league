import sys
from typing import NamedTuple

from src.textures import flat_sprite_maps, height_mapped_block


class ToolNames(NamedTuple):
    viewer = "level_viewer"
    height_map = "generate_heightmap"
    char_normals = "generate_character_normals"
    char_heights = "generate_character_heights"
    tile_normals = "generate_tile_normals"
    tile_heights = "generate_tile_heights"


# This conditional is just to ensure that when running a sprite generation tool,
# the level viewer import does not try to load assets which do not exist yet.
if sys.argv[-1] == "level_viewer":
    from src.tools import level_viewer

    registered_tools = {
        ToolNames.viewer: level_viewer.start,
        ToolNames.height_map: height_mapped_block.generate,
        ToolNames.char_normals: flat_sprite_maps.character_normals,
        ToolNames.char_heights: flat_sprite_maps.character_height_maps,
        ToolNames.tile_normals: flat_sprite_maps.tile_normals,
        ToolNames.tile_heights: flat_sprite_maps.tile_heights,
    }

else:
    registered_tools = {
        ToolNames.height_map: height_mapped_block.generate,
        ToolNames.char_normals: flat_sprite_maps.character_normals,
        ToolNames.char_heights: flat_sprite_maps.character_height_maps,
        ToolNames.tile_normals: flat_sprite_maps.tile_normals,
        ToolNames.tile_heights: flat_sprite_maps.tile_heights,
    }
