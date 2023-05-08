import pickle

from yaml import Loader, dump, load

from src.config import SAVE_FILE_DIRECTORY
from src.engine.guild import Guild
from src.engine.init_engine import eng


class GameStateRepository:
    @classmethod
    def save_file_path(cls, slot: int, fmt: str = "pikl") -> tuple[str, ...]:
        match fmt:
            case "pikl":
                return str(SAVE_FILE_DIRECTORY / f"save_{slot}.pikl")
            case "yaml":
                return str(SAVE_FILE_DIRECTORY / f"save_{slot}.yaml")
            case _:
                raise ValueError(
                    f"Unsupported format. Got {fmt=}, expected: pikl / yaml"
                )

    @classmethod
    def save_yaml(cls, slot: int, data: dict):
        if eng.current_room:
            raise RuntimeError("Cannot save game while in combat")

        path = cls.save_file_path(slot, fmt="yaml")
        with open(path, "w+") as save_file:
            dump(data, save_file)

    @classmethod
    def save_pikl(cls, slot: int, data: dict):
        if eng.current_room:
            raise RuntimeError("Cannot save game while in combat")

        path = cls.save_file_path(slot, fmt="pikl")
        with open(path, "wb+") as save_file:
            pickle.dump(data, save_file)

    @classmethod
    def load_yaml(cls, slot: int) -> Guild:
        path = cls.save_file_path(slot, fmt="yaml")
        with open(path, "r") as save_file:
            state = load(save_file, Loader)

        state = Guild.from_dict(state)

        return state

    @classmethod
    def load_pikl(cls, slot: int) -> Guild:
        path = cls.save_file_path(slot, fmt="pikl")
        with open(path, "rb") as save_file:
            state = pickle.load(save_file)

        state = Guild.from_dict(state)

        return state
