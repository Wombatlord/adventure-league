import arcade
from arcade.text import FontNameOrNames, Text
from arcade.types import Color


class TextureText:
    texture: arcade.Texture
    text: arcade.Text
    sprite: arcade.Sprite
    _sprite_list: arcade.SpriteList

    def __init__(
        self,
        text: str,
        start_x: float,
        lines: int,
        color: Color = arcade.color.WHITE,
        font_size: float = 12,
        width: int = 0,
        align: str = "left",
        font_name: FontNameOrNames = ("calibri", "arial"),
        bold: bool = False,
        italic: bool = False,
        anchor_x: str = "left",
        anchor_y: str = "baseline",
        multiline: bool = False,
        rotation: float = 0,
        start_z: float = 0,
    ):
        # breakpoint()
        self._sprite_list = arcade.SpriteList()
        self.text = Text(
            text,
            start_x,
            (lines - 1) * 16,  # Apparently it's this, not lines * 12
            color,
            12,
            width,
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
        size = (
            int(self.text.right - self.text.left),
            int(self.text.top - self.text.bottom),
        )

        self.draw_into_tex(size)

        self.sprite = arcade.Sprite(
            self.texture,
            center_x=self.text.right - (size[0] / 2),
            center_y=self.text.top,
        )
        scale = font_size / 12
        self.sprite.scale = scale
        self._sprite_list.append(self.sprite)

    @property
    def scale(self) -> float:
        return self.sprite.scale

    @scale.setter
    def scale(self, sc: float):
        self.sprite.scale = sc

    @property
    def center_x(self) -> float:
        return self.sprite.center_x

    @center_x.setter
    def center_x(self, x: float):
        self.sprite.center_x = x

    @property
    def center_y(self) -> float:
        return self.sprite.center_y

    @center_y.setter
    def center_y(self, y):
        self.sprite.center_y = y

    def draw_into_tex(self, size):
        self.texture = arcade.Texture.create_empty(self.text.text, size)
        texture_atlas = arcade.get_window().ctx.default_atlas
        texture_atlas.add(self.texture)

        with texture_atlas.render_into(self.texture) as fbo:
            fbo.clear((155, 155, 0, 0))
            self.text.draw()

    def draw(self):
        self._sprite_list.draw(pixelated=True)
