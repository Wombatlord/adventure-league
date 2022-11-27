import arcade
from src.engine.engine import eng

class MissionCard:
    def __init__(self, width, height, mission, margin, opacity=0):
        self.width = width
        self.height = height
        self.mission = mission
        self.margin = margin
        self.opacity = opacity


    def draw_card(self):


        y = (
                (self.margin + self.height) * self.mission
                + self.margin
                + self.height // 2
            )

        arcade.draw_rectangle_outline(
                center_x=self.width * 0.5,
                center_y=y / 3,
                width=self.width - self.margin,
                height=self.height * 0.3,
                color=(218, 165, 32, self.opacity),
            )

        arcade.Text(
                text=eng.mission_board.missions[self.mission].description,
                start_x=self.margin * 5,
                start_y=y / 3 + self.height * 0.11,
                font_name="Alagard",
            ).draw()

        arcade.Text(
                text="Boss: ",
                start_x=self.margin * 9,
                start_y=y / 3 + self.height * 0.05,
                font_name="Alagard",
                color=arcade.color.GOLDENROD
            ).draw()

        arcade.Text(
                text=f"{eng.mission_board.missions[self.mission].boss.name.name_and_title()}",
                start_x=self.margin * 20,
                start_y=y / 3 + self.height * 0.05,
                font_name="Alagard",
                color=arcade.color.RED
            ).draw()