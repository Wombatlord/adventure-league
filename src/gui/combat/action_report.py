from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, Iterable

import arcade
from pyglet.math import Vec2

from src.engine.events_enum import EventTopic
from src.engine.init_engine import eng
from src.entities.combat.leveller import Leveller
from src.entities.item.loot import Loot
from src.utils.rectangle import Corner, Rectangle
from src.world.level.dungeon import Dungeon


def linear_up_to_max(max_val: float, reached_at: float) -> Callable[[float], float]:
    gradient = max_val / reached_at
    return lambda x: max(0, min(x * gradient, max_val))


class XPGainWidget:
    _leveller: Leveller
    _text: arcade.Text
    _loot: Loot
    _xp_gain: int | float
    _intial_lvl: int
    _initial_xp: int
    _countdown_ms: float

    _display_xp: Callable[[float], float]

    ANIMATION_TIME_MS = 2500.0

    def __init__(self, dungeon: Dungeon, text: arcade.Text, leveller: Leveller):
        self._leveller = leveller
        self._loot = dungeon.loot

        self._xp_gain = dungeon.loot.calculate_xp_per_member(
            len(eng.game_state.team.members)
        ).xp_value
        if self._xp_gain == 0:
            self._xp_gain = dungeon.loot.awarded_xp_per_member

        self._initial_level = self._leveller.current_level
        self._initial_xp = self._leveller.total_xp
        self._text = text
        self._countdown_ms = self.ANIMATION_TIME_MS
        self._display_xp = linear_up_to_max(self._xp_gain, self.ANIMATION_TIME_MS)

    def update(self, dt: float) -> None:
        self.tick_xp()
        if self._countdown_ms < 0:
            return

        self._countdown_ms -= dt * 1000.0

    def tick_xp(self) -> None:
        time_left = self.ANIMATION_TIME_MS - self._countdown_ms
        delta_xp = int(self._display_xp(time_left)) - self._leveller.total_xp

        if delta_xp >= 1:
            self._leveller.gain_xp(delta_xp)
        levels = self._leveller.current_level - self._initial_level
        lvl_up = f"{' + ' + str(levels)}!" if levels else ""
        self._text.text = (
            f"{self._leveller.current_xp} / {self._leveller.xp_to_level_up} xp{lvl_up}"
        )

    def draw(self) -> None:
        self._text.draw()


class ActionReport(arcade.Section):
    survivor_labels: list[arcade.Text]
    xp_labels: list[arcade.Text]
    dungeon_context: Dungeon | None
    _xp_labels: list[XPGainWidget]

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
        self.dungeon_context = None
        self.survivor_labels = []
        self._xp_labels = []
        self.xp_labels = []
        self.zipped_labels = []
        self.xp_counter = 0
        self.window_dims = arcade.get_window().size
        self.bounds = Rectangle.from_limits(
            min_v=Vec2(self.window_dims[0] * 0.25, self.window_dims[1] * 0.25),
            max_v=Vec2(
                self.window_dims[0] - self.window_dims[0] * 0.25,
                self.window_dims[1] - self.window_dims[1] * 0.25,
            ),
        )

        self._pin, self._corner = None, None
        self.pin_corner(Corner.TOP_LEFT, self.get_offsets())

        self.title_text = arcade.Text(
            f"{title}",
            start_x=self.bounds.center.x,
            start_y=self.bounds.t - 50,
            anchor_x="center",
        )
        self.count_down = 0.025
        self._subscribe_to_events()

    def _subscribe_to_events(self):
        eng.combat_dispatcher.volatile_subscribe(
            topic=EventTopic.VICTORY,
            handler_id="ActionReport.after_action",
            handler=self.after_action,
        )

    def get_offsets(self) -> Callable[[], Vec2]:
        return lambda: Vec2(self.left, self.top)

    def pin_corner(self, corner: Corner, pin: Callable[[], Vec2]):
        self._pin = pin
        self._corner = corner

    def enable(self):
        if not self.enabled:
            self.enabled = True

    def after_action(self, event):
        self.dungeon_context = event[EventTopic.VICTORY][EventTopic.DUNGEON]
        xp_pre_victory: dict[str, Leveller] = event[EventTopic.VICTORY][
            EventTopic.TEAM_XP
        ]
        for i, survivor in enumerate(eng.game_state.team.members):
            y = 20 * i
            survivor_name_text = arcade.Text(
                f"{survivor.name}",
                start_x=self.bounds.l + 100,
                start_y=self.bounds.t - 100 - y,
            )
            xp_text = arcade.Text(
                "",
                start_x=self.bounds.r - 150,
                start_y=self.bounds.t - 100 - y,
            )
            self._xp_labels.append(
                XPGainWidget(
                    self.dungeon_context, xp_text, xp_pre_victory[survivor.name]
                )
            )
            self.survivor_labels.append(survivor_name_text)
            self.xp_labels.append(xp_text)

        self.enable()

    def animate_xp_counter(self):
        for i, label in enumerate(self.xp_labels):
            count = label.text.split("/")[0]
            if int(count) < self.dungeon_context.loot.awarded_xp_per_member:
                label.text = f"{int(count) + 1} / {eng.game_state.team.members[i].fighter.leveller.xp_to_level_up} xp"

    def on_update(self, delta_time: float):
        if not self.enabled:
            return
        for xp_widget in self._xp_labels:
            xp_widget.update(delta_time)

    def on_draw(self):
        arcade.draw_lrbt_rectangle_filled(
            self.left,
            self.width,
            self.bottom,
            self.height,
            color=(*arcade.color.RED[:3], 128),
        )
        self.title_text.draw()

        zipped_labels = zip(self.survivor_labels, self._xp_labels)

        for label_pair in zipped_labels:
            label_pair[0].draw()
            label_pair[1].draw()

    def on_resize(self, width, height):
        if not self._corner or not self._pin:
            return

        if not self.enabled:
            return

        self.window_dims = (width, height)
        self.left = width * 0.25
        self.bottom = height * 0.25

        self.width = width - width * 0.25
        self.height = height - height * 0.25

        self.bounds = self.bounds.from_limits(
            min_v=Vec2(self.window_dims[0] * 0.25, self.window_dims[1] * 0.25),
            max_v=Vec2(
                self.window_dims[0] - self.window_dims[0] * 0.25,
                self.window_dims[1] - self.window_dims[1] * 0.25,
            ),
        ).with_corner_at(self._corner, self._pin())

        self.title_text.position = self.bounds.center.x, self.bounds.t - 50

        labels = zip(self.survivor_labels, self.xp_labels)
        for i, label_pair in enumerate(labels):
            y = 20 * i
            label_pair[0].position = self.bounds.l + 100, self.bounds.t - 100 - y
            label_pair[1].position = self.bounds.r - 100, self.bounds.t - 100 - y

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    self.view.window.show_view(self.view.parent_factory())
