from __future__ import annotations

from typing import Callable, NamedTuple, TypeVar

import arcade
from arcade import Texture
from arcade.hitbox import BoundingHitBoxAlgorithm, HitBoxAlgorithm


class TextureSpec(NamedTuple):
    path: str

    @property
    def loaded(self) -> Texture:
        return _load_once(SpriteSheetSpecs, _load_texture_from_spec, self)


class SheetSpec(NamedTuple):
    args: tuple[str]
    kwargs: tuple[tuple[str, int | tuple | HitBoxAlgorithm], ...]

    @property
    def loaded(self) -> list[Texture]:
        return _load_once(SpriteSheetSpecs, _load_sheet_from_spec, self)

    def load_one(self, idx: int) -> Texture:
        return self.loaded[idx]


def _hashable(**d) -> tuple[tuple[str, int | tuple | HitBoxAlgorithm], ...]:
    return tuple(d.items())


class SingleTextureSpecs:
    _cache: dict[TextureSpec, Texture] = {}
    title_background = TextureSpec(
        "./assets/background_glacial_mountains.png",
    )

    banner = TextureSpec(
        "./assets/sprites/banner.png",
    )

    panel_highlighted = TextureSpec("./assets/sprites/panel.png")
    panel_darkened = TextureSpec("./assets/sprites/panel_dark.png")


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
    return arcade.load_texture(*spec)
