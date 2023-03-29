from typing import Callable

import arcade
from arcade import get_window
from arcade.gui import NinePatchTexture
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton, UITextureButton

from src.engine.init_engine import eng
from src.gui.window_data import WindowData


class CommandBarMixin:
    """
    Provides some methods to be implemented in any View which should have a command bar.

    Implementations should compose the buttons with attached handlers, labels, and styling
    ready to be added to the UIManager.
    """

    window: arcade.Window

    @property
    def command_bar(self) -> list[UIFlatButton]:
        ...


class PixelatedNinePatch(NinePatchTexture):
    """
    This only exists because I can't see any way to set the pixelated flag to True via the base NinePatchTexture.
    The implementation of draw_sized here is literally identical, the only difference is the default for the pixelated param.
    """

    def draw_sized(
        self,
        *,
        position: tuple[float, float] = (0, 0),
        size: tuple[float, float],
        pixelated: bool = True,
        **kwargs
    ):
        """
        Draw the 9-patch.

        :param size: size of the 9-patch
        """
        # TODO support to draw at a given position
        self.program.set_uniform_safe(
            "texture_id", self._atlas.get_texture_id(self._texture.atlas_name)
        )
        if pixelated:
            self._atlas.texture.filter = self._ctx.NEAREST, self._ctx.NEAREST
        else:
            self._atlas.texture.filter = self._ctx.LINEAR, self._ctx.LINEAR

        self.program["position"] = position
        self.program["start"] = self._left, self._bottom
        self.program["end"] = self.width - self._right, self.height - self._top
        self.program["size"] = size
        self.program["t_size"] = self._texture.size

        self._atlas.use_uv_texture(0)
        self._atlas.texture.use(1)
        self._geometry.render(self._program, vertices=1)


UIEventHandler = Callable[[UIEvent], None]


def nav_handler(target: type[arcade.View]) -> UIEventHandler:
    """An UIEventHandler which changes the View.

    Args:
        target (type[arcade.View]): The target View to switch to, received from the UIFlatButton this handler is attached to.

    Returns:
        UIEventHandler: An implementation of a handler for a UIEvent (eg. on_click, on_keypress etc.)
    """

    def _handle(event: UIEvent):
        get_window().show_view(target())

    return _handle


def nav_button(target: type[arcade.View], text: str) -> UITextureButton:
    """A generic button for changing to a different View.

    Args:
        target (type[arcade.View]): The target View to change to, passed to the click handler of the button.
        text (str): The text to render on the button, typically the name of the view that will be displayed on click.

    Returns:
        UITextureButton: A button with a text label and an attached click handler.
    """
    main_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[7]
    )
    pressed_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=3, texture=WindowData.buttons[9]
    )
    hovered_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[11]
    )

    btn = UITextureButton(
        text=text,
        texture=main_tex,
        texture_hovered=hovered_tex,
        texture_pressed=pressed_tex,
    )
    btn.on_click = nav_handler(target)

    return btn


def get_new_missions_handler(event: UIEvent) -> UIEventHandler:
    eng.refresh_mission_board()


def get_new_missions_button() -> UITextureButton:
    main_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[7]
    )
    pressed_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=3, texture=WindowData.buttons[9]
    )
    hovered_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[11]
    )
    btn = UITextureButton(
        text="New Missions",
        texture=main_tex,
        texture_hovered=hovered_tex,
        texture_pressed=pressed_tex,
    )
    btn.on_click = get_new_missions_handler

    return btn


def end_turn_handler(view) -> UIEventHandler:
    def _handle(event: UIEvent):
        if not view.target_selection and eng.awaiting_input:
            eng.next_combat_action()
            eng.awaiting_input = False
            return

        if not view.target_selection:
            return

        ok = view.target_selection.confirm()
        if ok:
            view.combat_grid_section.hide_path()
            view.target_selection = None
            view.item_menu_mode_allowed = True

    return _handle


def end_turn_button(view) -> UITextureButton:
    main_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[7]
    )
    pressed_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=3, texture=WindowData.buttons[9]
    )
    hovered_tex = PixelatedNinePatch(
        left=1, right=1, bottom=3, top=1, texture=WindowData.buttons[11]
    )

    btn = UITextureButton(
        text="CLICK ME TO ADVANCE!",
        texture=main_tex,
        texture_pressed=pressed_tex,
        texture_hovered=hovered_tex,
    )

    btn.on_click = end_turn_handler(view)

    return btn
