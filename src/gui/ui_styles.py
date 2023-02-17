from dataclasses import dataclass
from typing import Optional

import arcade
from arcade import Color
from arcade.gui import UIStyleBase
from arcade.text import FontNameOrNames

from src.gui.window_data import WindowData

"""
Module for declaring UI styling which can be provided to UI elements such as UIFlatButtons.
Default style is provided. To create a style compose a dict as in ADVENTURE_STYLE.
"""

@dataclass
class UIStyle(UIStyleBase):
    font_size: int = 12
    font_name: FontNameOrNames = WindowData.font
    font_color: Color = arcade.color.WHITE
    bg: Color = arcade.color.BLACK
    border: Optional[Color] = None
    border_width: int = 0

ADVENTURE_STYLE = {
        "normal": UIStyle(),
        "hover": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.GOLD,
            bg=(41, 39, 41),
            border=None,
            border_width=0,
        ),
        "press": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.GOLD,
            bg=arcade.color.BLACK,
            border=None,
            border_width=0,
        ),
        "disabled": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.WHITE,
            bg=arcade.color.GRAY,
            border=None,
            border_width=0,
        )
    }