from src.textures import height_mapped_block
from src.tools import level_viewer

registered_tools = {
    "level_viewer": level_viewer.start,
    "generate_heightmap": height_mapped_block.generate,
}
