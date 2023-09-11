from src.textures import flat_sprite_maps, height_mapped_block
from src.tools import level_viewer

registered_tools = {
    "level_viewer": level_viewer.start,
    "generate_heightmap": height_mapped_block.generate,
    "generate_character_normals": flat_sprite_maps.character_normals,
    "generate_character_heights": flat_sprite_maps.character_height_maps,
}
