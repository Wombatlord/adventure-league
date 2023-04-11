from typing import Callable, Generator

import arcade

from src.engine.init_engine import eng
from src.gui.components.scroll_window import gen_heights
from src.gui.window_data import WindowData
from src.projection import health

Hook = Callable[[], None]


class CombatScreen:
    def __init__(self) -> None:
        self.messages = []
        self.max_messages = 5
        self.heights = []
        self.message_id = 0
        self.time = 0
        self.team = eng.game_state.guild.team.members
        self.alpha_max = 255
        self.alphas = []

    def draw_stats(self):
        heights = self.msg_height()
        proj: health.HealthProjection = health.current()
        proj.configure(team=self.team, heights=[*heights]).draw()

    def msg_paint(self, n) -> list:
        if len(self.alphas) < len(self.messages) and len(self.alphas) < n:
            self.alphas.insert(0, self.alpha_max)
            self.alpha_max -= 50

    def msg_height(self) -> Generator[None, None, int]:
        return gen_heights(
            desc=False,
            row_height=40,
            y=0.25 * WindowData.height,
            spacing=2,
            max_height=WindowData.height / 2,
        )

    def draw_message(self):
        heights = self.msg_height()
        self.messages, alphas = eng.last_n_messages_with_alphas(self.max_messages)

        self.msg_paint(self.max_messages)
        for i, current_message in enumerate(self.messages):
            height = next(heights)
            if i == len(self.messages) - 1:
                paint = (218, 165, 32, alphas[-1])

            else:
                paint = (255, 255, 255, alphas[i])

            arcade.Text(
                text=current_message,
                start_x=WindowData.width / 2,
                start_y=height,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=500,
                align="center",
                color=paint,
                font_name=WindowData.font,
            ).draw()

    def draw_turn_prompt(self):
        color = (218, 165, 32, 255)

        if not eng.mission_in_progress:
            arcade.Text(
                text="Combat Over! Press G to return to the Guild",
                start_x=WindowData.width / 2,
                start_y=50,
                anchor_x="center",
                anchor_y="center",
                color=color,
                font_size=20,
                font_name=WindowData.font,
            ).draw()

        else:
            arcade.Text(
                text="PRESS SPACE TO ADVANCE!",
                start_x=WindowData.width / 2,
                start_y=50,
                anchor_x="center",
                anchor_y="center",
                color=color,
                font_size=20,
                font_name=WindowData.font,
            ).draw()