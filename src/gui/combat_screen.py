import arcade
from typing import NamedTuple, Callable, Generator
from src.engine.engine import eng
from src.gui.window_data import WindowData
from src.gui.gui_utils import gen_heights
from src.projection import health

Hook = Callable[[], None]

class MessageWithID(NamedTuple):
    message: str
    id: int

class CombatScreen:
    def __init__(self) -> None:
        self.messages = []
        self.latest_message = MessageWithID("No Message", 0)
        self.display_messages: list[MessageWithID] = []
        self.heights = []
        self.alphas = [255 - 50 * i for i in range(4)]
        self.alpha_max = 255
        self.alphas2 = []
        self.message_id = 0
        self.time = 0
        self.team = eng.guild.team.members
    
    def on_update(self, delta_time, hook: Hook):
        self.time += delta_time
        call_hook = True
        
        
        if self.time > 0.3:
            if call_hook:
                call_hook = hook()
            self.time = 0

    def draw_stats(self):
        heights = self.msg_height()
        proj: health.HealthProjection = health.current()
        proj.configure(heights=[*heights]).draw()
    
    def msg_paint2(self):
        for _ in range(len(self.messages) - 1):
            self.alphas2.insert(0, self.alpha_max)
            self.alpha_max -= 50

    def msg_paint(self) -> Generator[None, None, tuple[int, ...]]:
        # yield (218, 165, 32, 255)
        yield (255, 255, 255, 255)
        yield (255, 255, 255, 205)
        yield (255, 255, 255, 155)
        yield (255, 255, 255, 105)

    def msg_height(self) -> Generator[None, None, int]:
        return gen_heights(
            desc=False,
            row_height=40,
            y=0.25 * WindowData.height,
            spacing=2,
            max_height=WindowData.height / 2,
        )

    def draw_message(self):
        paint = (255, 255, 255, 255)
        heights = self.msg_height()
        messages, alphas = eng.last_n_messages_with_alphas(5)

        if any(msg != "" for msg in messages):
            
            for i, current_message in enumerate(messages):
                height = next(heights)
                if i == len(messages) - 1:
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

        arcade.Text(
                    text="PRESS SPACE TO ADVANCE!",
                    start_x=WindowData.width / 2,
                    start_y=50,
                    anchor_x="center",
                    anchor_y="center",
                    # multiline=True,
                    # width=500,
                    # align="center",
                    color=color,
                    font_size=20,
                    font_name=WindowData.font,
                ).draw()