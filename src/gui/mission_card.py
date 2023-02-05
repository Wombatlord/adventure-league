import arcade
from src.entities.dungeon import Dungeon


class MissionCard:
    mission: Dungeon
    def __init__(
        self,
        width,
        height,
        mission,
        margin,
        reserved_space,
        opacity=0,
    ):
        self.width = width
        self.height = height
        self.mission = mission
        self.margin = margin
        self.reserved_space = reserved_space
        self.opacity = opacity
        
    def draw_card(self, row):
        y = (
            (self.margin + self.height - self.reserved_space) * row
            + self.margin
            + (self.height - self.reserved_space) // 2
        )

        line_separation = 0.05*self.height

        arcade.draw_rectangle_outline(
            center_x=self.width * 0.5,
            center_y=y / 3 + self.reserved_space,
            width=self.width - self.margin,
            height=(self.height - self.reserved_space) * 0.3,
            color=(218, 165, 32, self.opacity),
        )
        cursor = [self.margin * 5, y / 3 + self.height*0.2]
        arcade.Text(
            text=self.mission.description,
            start_x=cursor[0],
            start_y=cursor[1],
            font_name="Alagard",
        ).draw()

        cursor[1] -= line_separation


        arcade.Text(
            text="Boss: ",
            start_x=self.margin * 9,
            start_y=cursor[1],
            font_name="Alagard",
            color=arcade.color.GOLDENROD,
        ).draw()

        
        arcade.Text(
            text=f"{self.mission.boss.name.name_and_title}",
            start_x=self.margin * 20,
            start_y=y / 3 + self.height * 0.15,
            font_name="Alagard",
            color=arcade.color.RED,
        ).draw()

        cursor[1] -= line_separation
        cursor[0] = self.margin * 9
        prefix = arcade.Text(
            text="Rewards:",
            start_x=cursor[0],
            start_y=cursor[1],
            font_name="Alagard",
        )
        prefix.draw()

        arcade.Text(
            text=self.mission.peek_reward(),
            start_x=cursor[0] + 16*self.margin,
            start_y=cursor[1],
            font_name="Alagard",
            color=arcade.color.GOLDENROD
        ).draw()

        