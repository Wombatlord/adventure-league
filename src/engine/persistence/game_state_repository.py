from yaml import Loader, dump, load

from src.config import SAVE_FILE_DIRECTORY
from src.engine.guild import Guild
from src.engine.init_engine import eng


class GameStateRepository:
    @classmethod
    def save_file_path(cls, slot: int) -> str:
        return str(SAVE_FILE_DIRECTORY / f"save_{slot}.yml")

    @classmethod
    def save(cls, slot: int):
        if eng.current_room:
            raise RuntimeError("Cannot save game while in combat")

        with open(cls.save_file_path(slot), "w+") as save_file:
            dump(eng.game_state.guild, save_file)

    @classmethod
    def load(cls, slot: int) -> Guild:
        with open(cls.save_file_path(slot), "r") as save_file:
            state = load(save_file, Loader)

        return state
