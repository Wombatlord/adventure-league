from typing import Generator

import arcade
from arcade.gui import Rect

from src.engine.events_enum import EventTopic
from src.engine.init_engine import eng
from src.gui.components.scroll_window import gen_heights
from src.gui.window_data import WindowData


class CombatLog:
    margin_x = 10
    margin_y = 10
    border_weight = 2

    def __init__(self, rect: Rect) -> None:
        self.rect = rect
        eng.subscribe(
            topic=EventTopic.MESSAGE,
            handler_id="combat_log.on_message_receieved",
            handler=self.on_message_receieved,
        )
        self.logs = []
        self.messages = []
        self.alphas = []
        self.alpha_max = 255
        self.shapes = arcade.shape_list.ShapeElementList()
        self.panel_bg = None
        self.panel_border = None
        self.refresh_ui()

    def refresh_ui(self):
        self.shapes.clear()
        self.make_shapes()
        self.shapes.append(self.panel_bg)
        self.shapes.append(self.panel_border)
        self.messages = []
        self.update_text()

    def make_shapes(self):
        rect = self.rect
        self.panel_bg = arcade.shape_list.create_rectangle_filled(
            center_x=rect.center_x,
            center_y=rect.center_y,
            width=rect.width - self.border_weight * 2,
            height=rect.height - self.border_weight * 2,
            color=(0, 50, 150, 100),
        )
        self.panel_border = arcade.shape_list.create_rectangle_outline(
            center_x=rect.center_x,
            center_y=rect.center_y,
            width=rect.width,
            height=rect.height,
            color=arcade.color.RED,
            border_width=self.border_weight,
        )

    def draw(self):
        self.shapes.draw()
        for message in self.messages:
            message.draw()

    def on_resize(self, w, h):
        self.rect = Rect(
            x=w - self.rect.width,
            y=h - self.rect.height,
            width=self.rect.width,
            height=self.rect.height,
        )
        self.refresh_ui()

    def on_message_receieved(self, event: dict):
        message = event.get(EventTopic.MESSAGE, "")
        if message:
            self.logs.append(message)
            self.logs = self.logs[-5:]
            self.update_text()

    def update_text(self):
        heights = self.msg_height()

        self.msg_paint(5)

        for i, current_message in enumerate(self.logs):
            height = next(heights)
            if i == len(self.logs) - 1:
                paint = (218, 165, 32, self.alphas[-1])
            else:
                paint = (255, 255, 255, self.alphas[i])

            txt = arcade.Text(
                text=current_message,
                start_x=self.rect.center_x,
                start_y=height,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=self.rect.width - 2 * self.margin_x,
                align="center",
                color=paint,
                font_name=WindowData.font,
            )

            self.messages.append(txt)
            self.messages = self.messages[-5:]

    def msg_paint(self, n) -> list:
        if len(self.alphas) <= len(self.messages) and len(self.alphas) < n:
            self.alphas.insert(0, self.alpha_max)
            self.alpha_max -= 50

    def msg_height(self) -> Generator[int, None, None]:
        return gen_heights(
            desc=True,
            row_height=40,
            y=self.rect.top + 40,
            spacing=2,
            max_height=WindowData.height,
        )
