from pathlib import Path
from unittest import TestCase

from src import config
from src.engine.persistence.game_state_repository import GuildRepository
from src.utils.profiling import profile_call

config.SAVE_FILE_DIRECTORY = Path("src") / "tests" / "benchmarks" / "fixtures"


class BenchmarkLoadTest(TestCase):
    def test_multiple_loads(self):
        self.load_many_saves()
        assert True

    @profile_call
    def load_many_saves(count=10):
        for _ in range(count):
            GuildRepository.load(slot=0)
