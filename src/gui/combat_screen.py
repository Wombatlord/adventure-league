import arcade
from src.engine.engine import eng
from src.gui.window_data import WindowData
from src.gui.gui_utils import gen_heights


class CombatScreen:
    def __init__(self) -> None:
        self.messages = eng.messages
        self.message = "None"
        self.display_messages = []
        self.heights = []

    def next_message(self):
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
            self.message = self.messages.pop(0)
            self.display_messages.append(self.message)

            if len(self.display_messages) > 5:
                self.display_messages.pop(0)

    def draw_message(self):
        # message = self.message

        if len(self.display_messages) > 0:
            for i, message in enumerate(self.display_messages):

                arcade.Text(
                    text=message,
                    start_x=WindowData.width / 2,
                    start_y=self.heights[i],
                    anchor_x="center",
                    anchor_y="center",
                    multiline=True,
                    width=500,
                    align="center",
                    font_name=WindowData.font,
                ).draw()
