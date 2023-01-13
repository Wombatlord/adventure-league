from src.entities.dungeon import Dungeon
from src.entities.dungeon_factory import create_random_dungeon


class MissionBoard:
    def __init__(self, size) -> None:
        self.size: int = size
        self.missions: list[Dungeon] = []

    def fill_board(self, enemy_amount) -> None:
        for _ in range(self.size):
            self.missions.append(create_random_dungeon(enemy_amount))

    def clear_board(self) -> None:
        self.missions = []

