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
        title = "Action Report"
        self.title_text = arcade.Text(
            f"{title}", start_x=self.width/2 + self.left / 2, start_y=self.height - 50, anchor_x="center"
        )
        self.surviving_fighters = []
        self.survivor_labels = []
        self.xp_labels = []

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
            survivor_name_text = arcade.Text(
                    f"{survivor.name}", start_x=self.left + 100, start_y=self.height - 100 - y
                )
            xp_text = arcade.Text(f"{dungeon.loot.awarded_xp_per_member}", start_x=self.width - 100, start_y=self.height - 100 - y)
            self.survivor_labels.append(survivor_name_text)
            self.xp_labels.append(xp_text)
        
        self.enable()

    def on_draw(self):
        arcade.draw_lrbt_rectangle_filled(
            self.left, self.width, self.bottom, self.height, color=arcade.color.RED
        )
        self.title_text.draw()
        labels = zip(self.survivor_labels, self.xp_labels)
        for label_pair in labels:
            label_pair[0].draw()
            label_pair[1].draw()

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    self.view.window.show_view(self.view.parent_factory())