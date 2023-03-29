from typing import Callable

import arcade
from arcade import Texture
from arcade.hitbox import BoundingHitBoxAlgorithm, HitBoxAlgorithm

SpriteSheetSpec = tuple[tuple[str], dict[str, int | tuple | HitBoxAlgorithm]]

SingleTextureSpec = tuple[str,]


class SingleTextureSpecs:
    title_background: SingleTextureSpec = ("./assets/background_glacial_mountains.png",)


class SpriteSheetSpecs:
    tiles: SpriteSheetSpec = (
        ("./assets/sprites/Isometric_MedievalFantasy_Tiles.png",),
        {
            "sprite_height": 17,
            "sprite_width": 16,
            "columns": 11,
            "count": 111,
            "margin": 0,
            "hit_box_algorithm": BoundingHitBoxAlgorithm,
        },
    )

    fighters: SpriteSheetSpec = (
        ("./assets/sprites/IsometricTRPGAssetPack_OutlinedEntities.png",),
        {
            "sprite_width": 16,
            "sprite_height": 16,
            "columns": 4,
            "count": 130,
            "margin": 1,
        },
    )

    buttons: SpriteSheetSpec = (
        ("./assets/sprites/buttons.png",),
        {
            "sprite_height": 16,
            "sprite_width": 48,
            "columns": 6,
            "count": 24,
            "margin": 0,
        },
    )

    indicators: SpriteSheetSpec = (
        ("./assets/sprites/TRPGIsometricAssetPack_MapIndicators.png",),
        {
            "sprite_height": 8,
            "sprite_width": 16,
            "columns": 2,
            "count": 6,
            "margin": 0,
        },
    )


def _load_sheet_from_spec(spec: SpriteSheetSpec) -> list[Texture]:
    args, kwargs = spec
    if not isinstance(args, tuple):
        raise TypeError(f"You have misconfigured a sprite sheet spec. {spec=}")
    hitbox_algorithm_class = kwargs.pop("hit_box_algorithm", None)
    hitbox_algo = None
    if hitbox_algorithm_class:
        hitbox_algo = hitbox_algorithm_class()

    return arcade.load_spritesheet(*args, **kwargs, hit_box_algorithm=hitbox_algo)


def _load_texture_from_spec(spec: SingleTextureSpec) -> Texture:
    return arcade.load_texture(*spec)


TextureData = None


class _LazyTextureData:
    __annotations__ = {
        **SpriteSheetSpecs.__annotations__,
        **SingleTextureSpecs.__annotations__,
    }
    loaders = {
        SpriteSheetSpecs: _load_sheet_from_spec,
        SingleTextureSpecs: _load_texture_from_spec,
    }

    def _load_if_specified(
        self, specs: type, loader: Callable, asset_name: str
    ) -> list[Texture] | Texture | None:
        if hasattr(specs, asset_name):
            asset = loader(getattr(specs, asset_name))
            setattr(self, asset_name, asset)
            return asset
        return None

    def __getattr__(self, attr_name: str) -> list[Texture] | Texture:
        try:
            for specs, loader in self.loaders.items():
                if asset := self._load_if_specified(
                    specs, loader, asset_name=attr_name
                ):
                    return asset
        except Exception:
            print(
                f"encountered error with {specs=} and {loader=} when trying to load asset {attr_name}"
            )
            raise

        raise AttributeError(f"Attempted to load undefined asset spec {attr_name}")


if TextureData is None:
    TextureData = _LazyTextureData()
