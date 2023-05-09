import pickle
from datetime import datetime
from enum import Enum
from os import path
from typing import NamedTuple

from yaml import Loader, dump, load

from src.config import SAVE_FILE_DIRECTORY, TEST_FILE_DIRECTORY
from src.engine.guild import Guild
from src.engine.persistence.dumpers import GameStateDumpers
from src.engine.persistence.loaders import GameStateLoaders

if not path.exists(SAVE_FILE_DIRECTORY):
    SAVE_FILE_DIRECTORY.mkdir(parents=True)


class Mode(NamedTuple):
    read: str
    write: str


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

    def mode(self) -> Mode:
        return {
            Format.YAML: Mode(read="r", write="w+"),
            Format.PICKLE: Mode(read="rb", write="wb+"),
        }[self]

    def dump(self, data, file_path):
        with open(file_path, self.mode().write) as save_file:
            dumper = self.dumper()
            dumper(data, save_file)

    def load(self, file_path) -> dict | list:
        with open(file_path, self.mode().read) as save_file:
            loader = self.loader()
            state = loader(save_file)

        return state


class GuildRepository:
    MAX_SLOTS = 3
    metadata_path = SAVE_FILE_DIRECTORY / "saves.yaml"

    @staticmethod
    def _get_default_metadata(max_slots: int):
        return [{"slot": slot} for slot in range(max_slots)]

    _latest_metadata = _get_default_metadata(MAX_SLOTS)

    @classmethod
    def save_file_path(
        cls, slot: int, fmt: Format = Format.PICKLE, testing=False
    ) -> str:
        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")

        if testing:
            return str(TEST_FILE_DIRECTORY / f"save_file_from_test_{slot}.{fmt.value}")

        return str(SAVE_FILE_DIRECTORY / f"save_{slot}.{fmt.value}")

    @classmethod
    def load(cls, slot, fmt=Format.PICKLE):
        if not (0 <= slot < cls.MAX_SLOTS):
            raise ValueError(
                f"Cannot load from slot {slot}, slot values must be one of {', '.join(*range(cls.MAX_SLOTS))}"
            )

        if not isinstance(fmt, Format):
            raise TypeError(f"Unrecognised format {fmt}")

        return GameStateLoaders.guild_from_dict(fmt.load(cls.save_file_path(slot, fmt)))

    @classmethod
    def save(
        cls,
        slot,
        guild_to_serialise: Guild,
        fmts: Format | tuple[Format, ...] = Format.PICKLE,
        testing=False,
    ):
        if not (0 <= slot < cls.MAX_SLOTS):
            raise ValueError(
                f"Cannot save to slot {slot}, slot values must be one of {', '.join(*range(cls.MAX_SLOTS))}"
            )
        if not isinstance(fmts, Format | tuple):
            raise TypeError(f"Unrecognised format {fmts}")

        if isinstance(fmts, Format):
            fmts = [fmts]

        if isinstance(fmts, tuple | list):
            for fmt in fmts:
                fmt.dump(
                    GameStateDumpers.guild_to_dict(guild_to_serialise),
                    cls.save_file_path(slot, fmt=fmt, testing=testing),
                )

        cls._update_metadata(guild_to_serialise, slot)

    @classmethod
    def get_slot_info(cls) -> list[dict]:
        return cls._load_metadata()

    @classmethod
    def _update_metadata(cls, guild: Guild, slot: int):
        metadata: list[dict] = cls._load_metadata()
        now = datetime.now()
        now_str = f"{now.month}/{now.day} {now.hour}:{now.minute}"
        metadata[slot] = {"name": guild.name, "slot": slot, "timestamp": now_str}
        cls._latest_metadata = metadata
        Format.YAML.dump(metadata, cls.metadata_path)

    @classmethod
    def _load_metadata(cls) -> list[dict]:
        metadata = cls._latest_metadata
        if path.exists(cls.metadata_path):
            metadata = Format.YAML.load(cls.metadata_path)
            if not metadata:
                metadata = cls._get_default_metadata(cls.MAX_SLOTS)
            cls._latest_metadata = metadata
        else:
            Format.YAML.dump(
                cls._get_default_metadata(cls.MAX_SLOTS), cls.metadata_path
            )

        return metadata
