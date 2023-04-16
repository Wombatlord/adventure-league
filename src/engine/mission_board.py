from src.world.level.dungeon import Dungeon
from src.world.level.dungeon_factory import create_dungeon_with_boss_room


class MissionBoard:
    def __init__(self, size) -> None:
        self.size: int = size
        self.missions: list[Dungeon] = []

    def fill_board(self, max_enemies_per_room, room_amount) -> None:
        for _ in range(self.size):
            self.missions.append(
                create_dungeon_with_boss_room(max_enemies_per_room, room_amount)
            )

    def clear_board(self) -> None:
        self.missions = []
