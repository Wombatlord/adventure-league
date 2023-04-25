import arcade
from arcade.gui import Rect

from src.engine.init_engine import eng


class CombatLog:
    margin_x = 10
    margin_y = 10
    border_weight = 2

    def __init__(self, rect: Rect) -> None:
        self.rect = rect
        eng.subscribe(
            topic="message",
            handler_id="combat_log.on_message_receieved",
            handler=self.on_message_receieved,
        )
        self.logs = []
        self.shapes = arcade.shape_list.ShapeElementList()
        self.panel_bg = None
        self.panel_border = None
        self.refresh_ui()
        self._do_update = False

    def refresh_ui(self):
        self.make_shapes()
        self.shapes.append(self.panel_bg)
        self.shapes.append(self.panel_border)
        self.make_text()

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

    def make_text(self):
        rect = self.rect
        self.text = arcade.Text(
            text="",
            start_x=rect.x + self.margin_x,
            start_y=rect.y + rect.height - self.margin_y,
            font_size=12,
            multiline=True,
            width=rect.width - 2 * self.margin_x,
        )

    def draw(self):
        self.shapes.draw()
        self.text.draw()

    def on_message_receieved(self, event: dict):
        self._do_update = True
        message = event.get("message", "")
        if message:
            self.logs.append(message)
            self.logs.append("")

    def on_update(self):
        if not self._do_update:
            return
        self._do_update = False
        self.update_text()

    def on_resize(self, w, h):
        self.rect = Rect(
            x=w - self.rect.width,
            y=h - self.rect.height,
            width=self.rect.width,
            height=self.rect.height,
        )
        self.refresh_ui()
        self._do_update = True

    def update_text(self):
        self.text.text = ""
        for line in self.logs:
            self.text.text = self.text.text + "\n" + line

        if (
            self.text.content_height > self.rect.height - 2 * self.margin_y
            and self.logs
        ):
            self.logs = self.logs[1:]
            self.update_text()
