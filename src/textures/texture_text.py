import functools
from types import FunctionType
from typing import Dict, Optional, Self, Union

import arcade
from arcade import Texture
from arcade.gui import (
    NinePatchTexture,
    Property,
    Surface,
    UIAnchorLayout,
    UIInteractiveWidget,
    UILabel,
    UIStyleBase,
    UIStyledWidget,
    UITextureButton,
    UITextWidget,
    UIWidget,
    bind,
)
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

    def __enter__(self):
        # return self._text.__enter__()
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self._text.__exit__(exc_type, exc_val, exc_tb)
        pass

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
        print("SPRITE SETUP")
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

        with texture_atlas.render_into(self.texture) as fbo:
            fbo.clear((155, 155, 0, 0))
            self._text.draw()

    def draw(self):
        print("DRAW")
        if self._has_changed:
            self.render()
        self._sprite_list.draw(pixelated=True)


class TXUILabel(UILabel):
    @functools.wraps(UILabel.__init__)
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        text: str = "",
        font_name=("Arial",),
        font_size: float = 12,
        text_color: Color = (255, 255, 255, 255),
        bold=False,
        italic=False,
        align="left",
        multiline: bool = False,
        size_hint=None,
        size_hint_min=None,
        size_hint_max=None,
        **kwargs,
    ):
        self.label = TextureText.create(
            start_x=0,
            text=text,
            lines=len(text.split("\n")),
            font_name=font_name,
            font_size=font_size,
            color=text_color,
            width=width,
            bold=bold,
            italic=italic,
            align=align,
            anchor_y="bottom",  # position text bottom left, to fit into scissor box
            multiline=multiline,
            **kwargs,
        )

        UIWidget.__init__(
            self,
            x=x,
            y=y,
            width=width or self.label.content_width,
            height=height or self.label.content_height,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            **kwargs,
        )

        # set label size, if the width or height was given
        # because border and padding can only be applied later, we can avoid `fit_content()`
        # and set with and height separately
        if width:
            self.label.width = int(width)
        if height:
            self.label.height = int(height)
        bind(self, "rect", self._update_layout)

    def fit_content(self):
        pass


class TXUITextWidget(UITextWidget):
    def __init__(self, text: str = "", multiline: bool = False, **kwargs):
        UIAnchorLayout.__init__(self, text=text, **kwargs)
        self._label = TXUILabel(
            text=text,
            multiline=multiline,
            width=1000,
            font_size=kwargs.get("font_size", 36),
        )
        self.add(self._label)
        self.ui_label.fit_content()
        bind(self, "rect", self.ui_label.fit_content)


class TXUInteractiveWidget(UIInteractiveWidget):
    """
    Base class for widgets which use mouse interaction (hover, pressed, clicked)

    :param float x: x coordinate of bottom left
    :param float y: y coordinate of bottom left
    :param width: width of widget
    :param height: height of widget
    :param size_hint: Tuple of floats (0.0-1.0), how much space of the parent should be requested
    :param size_hint_min: min width and height in pixel
    :param size_hint_max: max width and height in pixel:param x: center x of widget
    :param style: not used
    """

    # States
    hovered = Property(False)
    pressed = Property(False)
    disabled = Property(False)

    def __init__(
        self,
        *,
        x: float = 0,
        y: float = 0,
        width: float,
        height: float,
        size_hint=None,
        size_hint_min=None,
        size_hint_max=None,
        **kwargs,
    ):
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            **kwargs,
        )
        self.register_event_type("on_click")

        bind(self, "pressed", self.trigger_render)
        bind(self, "hovered", self.trigger_render)
        bind(self, "disabled", self.trigger_render)


class TXUITextureButton(
    UITextureButton,
    TXUInteractiveWidget,
    UIStyledWidget["UITextureButton.UIStyle"],
    TXUITextWidget,
):
    def get_current_state(self) -> str:
        return UITextureButton.get_current_state(self)

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        texture: Union[None, Texture, NinePatchTexture] = None,
        texture_hovered: Union[None, Texture, NinePatchTexture] = None,
        texture_pressed: Union[None, Texture, NinePatchTexture] = None,
        texture_disabled: Union[None, Texture, NinePatchTexture] = None,
        text: str = "",
        multiline: bool = False,
        scale: Optional[float] = None,
        style: Optional[Dict[str, UIStyleBase]] = None,
        size_hint=None,
        size_hint_min=None,
        size_hint_max=None,
        **kwargs,
    ):
        if width is None and texture is not None:
            width = texture.size[0]

        if height is None and texture is not None:
            height = texture.size[1]

        if width is None:
            raise ValueError("Unable to determine a width.")
        if height is None:
            raise ValueError("Unable to determine a height.")

        if scale is not None and texture is not None:
            width = texture.size[0] * scale
            height = texture.size[1] * scale

        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            style=style or UITextureButton.DEFAULT_STYLE,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            text=text,
            multiline=multiline,
            **kwargs,
        )

        self._textures = {}

        if texture:
            self._textures["normal"] = texture
            self._textures["hover"] = texture
            self._textures["press"] = texture
            self._textures["disabled"] = texture
        if texture_hovered:
            self._textures["hover"] = texture_hovered
        if texture_pressed:
            self._textures["press"] = texture_pressed
        if texture_disabled:
            self._textures["disabled"] = texture_disabled

        bind(self, "_textures", self.trigger_render)
