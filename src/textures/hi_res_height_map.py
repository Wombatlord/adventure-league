from src.textures.texture_data import SingleTextureSpecs
from skimage import io, util
import numpy as np


CHANNEL_MIN = 0
CHANNEL_MAX = (1 << 16) - 1
STEP = 16


def generate_height_map(path: str = SingleTextureSpecs.tile_normals_hi_res.args[0]):
    image = util.img_as_uint(io.imread(path))

    
