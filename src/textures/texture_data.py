from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, NamedTuple, Self, TypeVar

import arcade
from arcade import Texture
from arcade.hitbox import BoundingHitBoxAlgorithm, HitBoxAlgorithm
from arcade.types import PointList
from PIL.Image import Image
from pyglet.math import Vec2


def _hashable(**d) -> tuple[tuple[str, int | tuple | HitBoxAlgorithm], ...]:
    return tuple(d.items())


class TileHitBoxAlgorithm(HitBoxAlgorithm):
    name = "tile"
    cache = True
    tile_dims: tuple[int, int, int]

    def __init__(self, tile_dims: tuple[int, int, int] = (16, 8, 8)) -> None:
        self.tile_dims = tile_dims
        self._cache_name = f"{self.__class__.__name__}{tile_dims}"

    def calculate(self, image: Image, **kwargs) -> PointList:
        top = self.tile_dims[2]
        width = self.tile_dims[0]
        points = (
            Vec2(-width / 2, top - self.tile_dims[1] / 2),
            Vec2(0, top),
            Vec2(width / 2, top - self.tile_dims[1] / 2),
            Vec2(0, top - self.tile_dims[1]),
        )
        scale_factor = 17 / 16
        translation = Vec2(0, -0.5)
        return [tuple(v * scale_factor + translation) for v in points]

    def __call__(self, *args, **kwargs) -> Self:
        return super().__call__(*args, **kwargs)

    @property
    def param_str(self) -> str:
        return f"{self.tile_dims}"


class TextureSpec(NamedTuple):
    args: tuple[Any]
    kwargs: tuple[tuple[str, int | tuple | HitBoxAlgorithm], ...] = _hashable()

    @property
    def loaded(self) -> Texture:
        return _load_once(SpriteSheetSpecs, _load_texture_from_spec, self)


class SheetSpec(NamedTuple):
    args: tuple[str]
    kwargs: tuple[tuple[str, int | tuple | HitBoxAlgorithm], ...]

    @property
    def loaded(self) -> list[Texture]:
        return _load_once(SpriteSheetSpecs, _load_sheet_from_spec, self)

    def get_normals(self) -> SheetSpec | None:
        path = Path(self.args[0].replace(".png", ".norm.png"))
        if not path.exists():
            return None
        return SheetSpec((path,), self.kwargs)

    def get_height_map(self) -> SheetSpec | None:
        path = Path(self.args[0].replace(".png", ".z.png"))
        if not path.exists():
            return None
        return SheetSpec((path,), self.kwargs)

    def load_one(self, idx: int) -> Texture:
        return self.loaded[idx]


class ExplicitHitBox(HitBoxAlgorithm):
    points: PointList = ()

    def __init__(self):
        super().__init__()

    def calculate(self, image: Image, **kwargs) -> PointList:
        return self.points


class NormalsHitBox(ExplicitHitBox):
    points = [
        tuple(offset)
        for offset in [Vec2(i * 16, j * 17) / 2 for i in (-1, 1) for j in (-1, 1)]
    ]


class SingleTextureSpecs:
    _cache: dict[TextureSpec, Texture] = {}
    title_background = TextureSpec(args=("./assets/background_glacial_mountains.png",))

    title_banner = TextureSpec(
        args=("./assets/sprites/banner.png",),
    )

    start_banner = TextureSpec(args=("./assets/sprites/start_banner.png",))
    panel_highlighted = TextureSpec(args=("./assets/sprites/panel.png",))
    panel_darkened = TextureSpec(args=("./assets/sprites/panel_dark.png",))
    mercenaries_banner = TextureSpec(args=("./assets/sprites/mercenaries_banner.png",))
    mission_banner = TextureSpec(args=("./assets/sprites/mission_banner.png",))
    mission_banner_dark = TextureSpec(args=("./assets/sprites/mission_banner.png",))
    health_bar = TextureSpec(args=("./assets/sprites/health_bar.png",))
    tile_normals = TextureSpec(
        args=("./assets/sprites/tile_normals.png",),
        kwargs=_hashable(
            x=0,
            y=0,
            width=16,
            height=17,
            hit_box_algorithm=BoundingHitBoxAlgorithm,
        ),
    )
    tile_normals_hi_res = TextureSpec(
        args=("./assets/sprites/tile_normals_hi_res.png",)
    )


class SpriteSheetSpecs:
    _cache: dict[SheetSpec, list[Texture]] = {}
    tiles = SheetSpec(
        args=("./assets/sprites/Isometric_MedievalFantasy_Tiles.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 17,
                "sprite_width": 16,
                "columns": 11,
                "count": 111,
                "margin": 0,
                "hit_box_algorithm": TileHitBoxAlgorithm,
            }
        ),
    )

    pillar_normals = SheetSpec(
        args=("./assets/sprites/Isometric_MedievalFantasy_Tiles.norm.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 17,
                "sprite_width": 16,
                "columns": 11,
                "count": 111,
                "margin": 0,
                "hit_box_algorithm": TileHitBoxAlgorithm,
            }
        ),
    )

    tile_saturation_gradient = SheetSpec(
        args=("./assets/sprites/tile_normals_saturation_gradient.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 17,
                "sprite_width": 16,
                "columns": 1,
                "count": 8,
                "margin": 0,
                "hit_box_algorithm": BoundingHitBoxAlgorithm,
            }
        ),
    )
    tile_height_map_sheet = SheetSpec(
        args=("./assets/sprites/tile_height_map_sheet.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 17,
                "sprite_width": 16,
                "columns": 1,
                "count": 8,
                "margin": 0,
                "hit_box_algorithm": BoundingHitBoxAlgorithm,
            }
        ),
    )
    tile_normals_2_layer = SheetSpec(
        args=("./assets/sprites/tile_normals_2_layer.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 17,
                "sprite_width": 16,
                "columns": 2,
                "count": 2,
                "margin": 0,
                "hit_box_algorithm": BoundingHitBoxAlgorithm,
            }
        ),
    )

    characters = SheetSpec(
        args=("./assets/sprites/IsometricTRPGAssetPack_OutlinedEntities.png",),
        kwargs=_hashable(
            **{
                "sprite_width": 16,
                "sprite_height": 16,
                "columns": 4,
                "count": 130,
                "margin": 1,
            }
        ),
    )

    buttons = SheetSpec(
        args=("./assets/sprites/buttons_scaled.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 32,
                "sprite_width": 96,
                "columns": 6,
                "count": 24,
                "margin": 0,
            }
        ),
    )

    indicators = SheetSpec(
        args=("./assets/sprites/TRPGIsometricAssetPack_MapIndicators.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 8,
                "sprite_width": 16,
                "columns": 2,
                "count": 6,
                "margin": 0,
            }
        ),
    )

    icons = SheetSpec(
        args=("./assets/sprites/IsometricTRPGAssetPack_UI.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 8,
                "sprite_width": 8,
                "columns": 10,
                "count": 110,
                "margin": 0,
            }
        ),
    )

    banners = SheetSpec(
        args=("./assets/sprites/banner_sheet.png",),
        kwargs=_hashable(
            **{
                "sprite_height": 31,
                "sprite_width": 193,
                "columns": 1,
                "count": 4,
                "margin": 0,
            }
        ),
    )


_Loaded_T = TypeVar("_Loaded_T", bound=object)
_Spec_T = TypeVar("_Spec_T", bound=tuple)


def _load_once(cls, loader: Callable[[_Spec_T], _Loaded_T], spec) -> _Loaded_T:
    if hit := cls._cache.get(spec):
        return hit
    else:
        hit = loader(spec)
        cls._cache[spec] = hit

        return hit


def _load_sheet_from_spec(spec: SheetSpec) -> list[Texture]:
    args, kwargs = spec
    kwargs = dict(kwargs)
    if not isinstance(args, tuple):
        raise TypeError(f"You have misconfigured a sprite sheet spec. {spec=}")
    hitbox_algorithm_class = kwargs.pop("hit_box_algorithm", None)
    hitbox_algo = None
    if hitbox_algorithm_class:
        hitbox_algo = hitbox_algorithm_class()

    return arcade.load_spritesheet(*args, **kwargs, hit_box_algorithm=hitbox_algo)


def _load_texture_from_spec(spec: TextureSpec) -> Texture:
    kwargs = dict(spec.kwargs)
    if "hit_box_algorithm" in kwargs:
        kwargs["hit_box_algorithm"] = kwargs["hit_box_algorithm"]()
    return arcade.load_texture(*spec.args, **kwargs)
