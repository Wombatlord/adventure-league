from typing import Iterable
import arcade

from src.engine.init_engine import eng
from src.world.level.dungeon import Dungeon


class ActionReport(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        *,
        name: str | None = None,
        accept_keyboard_keys: bool | Iterable = True,
        accept_mouse_events: bool | Iterable = True,
        prevent_dispatch: Iterable | None = None,
        prevent_dispatch_view: Iterable | None = None,
        local_mouse_coordinates: bool = False,
        enabled: bool = False,
        modal: bool = True,
        draw_order: int = 10,
    ):
        super().__init__(
            left,
            bottom,
            width,
            height,
            name=name,
            accept_keyboard_keys=accept_keyboard_keys,
            accept_mouse_events=accept_mouse_events,
            prevent_dispatch=prevent_dispatch,
            prevent_dispatch_view=prevent_dispatch_view,
            local_mouse_coordinates=local_mouse_coordinates,
            enabled=enabled,
            modal=modal,
            draw_order=draw_order,
        )
        self.title = "Action Report"
        self.title_text = None
        self.surviving_fighters = []
        self.survivor_labels = []

        self._subscribe_to_events()

    def _subscribe_to_events(self):
        eng.combat_dispatcher.volatile_subscribe(
            topic="team triumphant",
            handler_id="ActionReport.after_action",
            handler=self.after_action,
        )

    def enable(self):
        if not self.enabled:
            self.enabled = True

    def after_action(self, event):
        dungeon: Dungeon = event["team triumphant"]["dungeon"]

        for i, survivor in enumerate(eng.game_state.team.members):
            y = 20 * i
            t = arcade.Text(
                    f"{survivor.name}", start_x=self.width / 2, start_y=self.height - 50 - y
                )
            self.survivor_labels.append(t)

        self.title_text = arcade.Text(
            f"{self.title}", start_x=self.width / 2, start_y=self.height - 50
        )
        self.enable()

    def on_draw(self):
        arcade.draw_lrbt_rectangle_filled(
            self.left, self.width, self.bottom, self.height, color=arcade.color.RED
        )
        self.title_text.draw()
        for t in self.survivor_labels:
            t.draw()
