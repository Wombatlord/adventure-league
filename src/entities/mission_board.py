from src.entities.dungeon import Dungeon
from src.entities.dungeon_factory import create_random_dungeon


class MissionBoard:
    def __init__(self, size) -> None:
        self.size: int = size
        self.missions: list[Dungeon] = []

    def fill_board(self, enemy_amount) -> None:
        for i in range(self.size):
            self.missions.append(create_random_dungeon(enemy_amount, dungeon_id=i))

    def clear_board(self) -> None:
        self.missions = []

    def get_mission_by_id(self, id) -> Dungeon:
        # UNTESTED. Select and return a dungeon by id.
        for dungeon in self.missions:
            if id == dungeon.id:
                return dungeon
        
        raise ValueError("No matching ID")

    def remove_mission_by_id(self, id) -> None:
        # UNTESTED. Clear a dungeon from the missions array
        for i, dungeon in enumerate(self.missions):
            if id == dungeon.id:
                self.missions.pop(i)
