import pickle
from enum import Enum

from yaml import Loader, dump, load

from src.config import SAVE_FILE_DIRECTORY, TEST_FILE_DIRECTORY
from src.engine.guild import Guild
from src.engine.persistence.dumpers import GameStateDumpers
from src.engine.persistence.loaders import GameStateLoaders


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
            Format.PICKLE: lambda file: pickle.load(file),
        }[self]

    def dump(self, data, path):
        if self == Format.PICKLE:
            mode = "wb+"
        else:
            mode = "w+"

        with open(path, mode) as save_file:
            dumper = self.dumper()
            dumper(data, save_file)

    def load(self, path) -> dict:
        with open(path, "rb") as save_file:
            loader = self.loader()
            state = loader(save_file)

        return state


class GameStateRepository:
    @classmethod
    def save_file_path(
        cls, slot: int, fmt: Format = Format.PICKLE, testing=False
    ) -> tuple[str, ...]:
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")

        if testing:
            return str(TEST_FILE_DIRECTORY / f"save_file_from_test_{slot}.{fmt.value}")

        return str(SAVE_FILE_DIRECTORY / f"save_{slot}.{fmt.value}")

    @classmethod
    def load(cls, slot, fmt=Format.PICKLE):
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")

        return GameStateLoaders.guild_from_dict(fmt.load(cls.save_file_path(slot, fmt)))

    @classmethod
    def save(
        cls,
        slot,
        fmts: Format | tuple[Format, ...] = Format.PICKLE,
        guild_to_serialise: Guild = None,
        testing=False,
    ):
        if not isinstance(fmts, Format | tuple):
            raise TypeError(f"Unrecognised format {fmt}")

        if isinstance(fmts, Format):
            fmts.dump(
                GameStateDumpers.guild_to_dict(guild_to_serialise),
                cls.save_file_path(slot, testing=testing),
            )
            return

        elif isinstance(fmts, tuple):
            for fmt in fmts:
                fmt.dump(
                    GameStateDumpers.guild_to_dict(guild_to_serialise),
                    cls.save_file_path(slot, fmt=fmt, testing=testing),
                )
