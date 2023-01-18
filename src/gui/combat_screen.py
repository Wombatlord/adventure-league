import arcade
from typing import NamedTuple
from src.engine.engine import eng
from src.gui.window_data import WindowData
from src.gui.gui_utils import gen_heights

class MessageWithID(NamedTuple):
    message: str
    id: int

class CombatScreen:
    def __init__(self) -> None:
        self.messages = eng.messages
        self.latest_message = MessageWithID("No Message", 0)
        self.display_messages: list[MessageWithID] = []
        self.heights = []
        self.alphas = []
        self.alpha_max = 255
        self.message_id = 0
        self.time = 0
        self.turn_prompt = True

    def on_update(self, delta_time):
        self.time += delta_time
        if self.time > 2:
            self.progress_message_deque()
            self.time = 0
    
    def progress_message_deque(self):
        if len(self.heights) == 0:
            heights = gen_heights(
                desc=False,
                row_height=40,
                y=WindowData.height / 2,
                spacing=2,
                max_height=WindowData.height,
            )
            for height in heights:
                print(height)
                self.heights.append(height)

        if len(self.messages) > 0:
            self.turn_prompt = False
            self.latest_message = MessageWithID(self.messages.pop(0), self.message_id)
            self.display_messages.append(self.latest_message)
            self.message_id += 1
            if len(self.display_messages) > 5:
                self.display_messages.pop(0)
        
        if len(self.messages) == 0:
            self.turn_prompt = True
        
        if len(self.alphas) < 4:
            self.alphas.insert(0, self.alpha_max)
            self.alpha_max -= 50
    
    def draw_message(self):
        if len(self.display_messages) > 0:
            for i, current_message in enumerate(self.display_messages):
                
                if current_message.message == self.latest_message.message and current_message.id == self.latest_message.id:
                    color = (218, 165, 32, 255)
                else:
                    color = (255,255,255, self.alphas[i])
                
                arcade.Text(
                    text=current_message.message,
                    start_x=WindowData.width / 2,
                    start_y=self.heights[i],
                    anchor_x="center",
                    anchor_y="center",
                    multiline=True,
                    width=500,
                    align="center",
                    color=color,
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