import pickle

from yaml import Loader, dump, load

from src.config import SAVE_FILE_DIRECTORY
from src.engine.guild import Guild
from src.engine.init_engine import eng
from src.engine.persistence.loaders import GameStateLoaders

from enum import Enum

class Format(Enum):
    YAML = "yaml"
    PICKLE = "pikl"
    
    def dumper(self):
        return {
            Format.YAML: dump,
            Format.PICKLE: pickle.dump,
        }[self]
        
    def loader(self):
        return {
            Format.YAML: lambda file: load(file, Loader),
            Format.PICKLE: pickle.load,
        }[self]
    
    def dump(self, data, path):
        with open(path, "wb+") as save_file:
            self.dumper(data, save_file)
            
     def load(self, path) -> dict:
         with open(path, "r") as save_file:
            state = self.loader(save_file)
            
         return state
        

class GameStateRepository:
    @classmethod
    def save_file_path(cls, slot: int, fmt: Format = Format.PICKLE) -> tuple[str, ...]:
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")
        return str(SAVE_FILE_DIRECTORY / f"save_{slot}.{fmt.value}")
    
    @classmethod
    def load(cls, slot, fmt=Format.PICKLE):
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")
            
        return GameStateLoaders.guild_from_dict(fmt.load(self.save_file_path(slot, fmt)))
        
        
    @classmethod
    def save(cls, slot, state, fmt=Format.PICKLE):
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")
            
        fmt.dump(GameStateDumpers.guild_to_dict(state))

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

        state = GameStateLoaders.guild_from_dict(state)
        return state
