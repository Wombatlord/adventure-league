import functools
from types import FunctionType
from typing import Self

import arcade
from arcade.text import FontNameOrNames, Text
from arcade.types import Color


class TextureText:
    texture: arcade.Texture | None
    _text: arcade.Text
    sprite: arcade.Sprite | None
    _sprite_list: arcade.SpriteList

    @staticmethod
    def redraw(method: FunctionType):
        @functools.wraps(method)
        def _decorated(_self, *args):
            _self._has_changed = True
            return method(_self, *args)

        return _decorated

    @classmethod
    def create(
        cls,
        text: str,
        start_x: float,
        lines: int,
        color: Color = arcade.color.WHITE,
        font_size: float = 12,
        width: float | int = 0,
        align: str = "left",
        font_name: FontNameOrNames = ("calibri", "arial"),
        bold: bool = False,
        italic: bool = False,
        anchor_x: str = "left",
        anchor_y: str = "baseline",
        multiline: bool = False,
        rotation: float = 0,
        start_z: float = 0,
        **_,
    ) -> Self:
        text = Text(
            text,
            start_x,
            (lines - 1) * 16,  # Apparently it's this, not lines * 12
            color,
            12,
            1000,
            align,
            font_name,
            bold,
            italic,
            anchor_x,
            anchor_y,
            multiline,
            rotation,
            start_z=start_z,
        )
        return cls(text, font_size=font_size)

    def __init__(
        self,
        text: arcade.Text,
        font_size: float = 12,
    ):
        self._font_size = font_size

        self._sprite_list = arcade.SpriteList()
        self._text = text
        self.texture = None
        self.sprite = None
        self._has_changed = True
        self.render()

    def calculate_size(self):
        return (
            int(self._text.right - self._text.left),
            int(self._text.top - self._text.bottom),
        )

    def render(self):
        if not self._has_changed:
            return
        size = self.calculate_size()
        self.draw_into_tex(size)
        self.setup_sprite(size)
        self._has_changed = False

    def setup_sprite(self, size):
        center_x = self.center_x or self._text.right - (size[0] / 2)
        center_y = self.center_y or self._text.top
        if not self.sprite:
            self.sprite = arcade.Sprite(
                self.texture,
                center_x=center_x,
                center_y=center_y,
            )
        else:
            self.sprite.texture = self.texture
            self.sprite.center_x, self.sprite.center_y = center_x, center_y

        self.sprite.scale = self.scale
        self._sprite_list.clear()
        self._sprite_list.append(self.sprite)

    @property
    def text(self) -> str:
        return self._text.text

    @text.setter
    @redraw
    def text(self, value: str):
        self._text.text = value

    @property
    def scale(self) -> float:
        return self._font_size / 12

    @scale.setter
    def scale(self, sc: float):
        self._font_size = 12 * sc
        self.sprite.scale = sc

    @property
    def center_x(self) -> float | None:
        return self.sprite.center_x if self.sprite else None

    @center_x.setter
    def center_x(self, x: float):
        self.sprite.center_x = x

    @property
    def center_y(self) -> float | None:
        return self.sprite.center_y if self.sprite else None

    @center_y.setter
    def center_y(self, y):
        self.sprite.center_y = y

    @property
    def font_name(self) -> str:
        return self._text.font_name

    @font_name.setter
    @redraw
    def font_name(self, name: str):
        self._text.font_name = name

    @property
    def font_size(self) -> float:
        return self._font_size

    @font_size.setter
    @redraw
    def font_size(self, value: float):
        print(f"FONT SIZE SET: {value=}")
        self._font_size = value
        self.sprite.scale = self.scale

    @property
    def color(self):
        return self._text.color

    @color.setter
    @redraw
    def color(self, value: Color):
        self._text.color = value

    @property
    def content_width(self) -> float:
        content_width = self.width
        print(f"GETTER: {content_width=}, {self.font_size=}")
        return content_width

    @property
    def content_height(self) -> float:
        return self.height

    @property
    def width(self) -> float:
        width = self.sprite.width
        print(f"GETTER: {width=}, {self.font_size=}")
        return width

    @width.setter
    @redraw
    def width(self, width: int):
        print(f"SETTER: {width=}")
        self.font_size *= width / self.width
        self.sprite.scale = self.scale

    @property
    def height(self) -> float:
        return self.sprite.height / 4

    @height.setter
    @redraw
    def height(self, value: int):
        print(f"HEIGHT_SETTER: {value=}, {self.height=}, {value/self.height=}")
        self.font_size = value - 2
        self.sprite.scale = self.scale
        print(f"f{self.font_size=}")

    def draw_into_tex(self, size):
        if not self.texture:
            self.texture = arcade.Texture.create_empty(self._text.text, size)
            texture_atlas = arcade.get_window().ctx.default_atlas
            texture_atlas.add(self.texture)

        with self._sprite_list.atlas.render_into(self.texture) as fbo:
            fbo.clear((155, 155, 0, 0))
            self._text.draw()

    def draw(self):
        print("DRAW")
        if self._has_changed:
            self.render()
        self._sprite_list.draw(pixelated=True)
