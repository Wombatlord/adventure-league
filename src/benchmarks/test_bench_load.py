import pstats
from datetime import datetime
from pathlib import Path
from unittest import TestCase

from viztracer import VizTracer

from src import config
from src.engine.persistence.game_state_repository import GuildRepository

config.SAVE_FILE_DIRECTORY = Path("src") / "tests" / "benchmarks" / "fixtures"


class BenchmarkLoadTest(TestCase):
    def test_load(self):
        with VizTracer(output_file="profiles/test_load_profile.json"):
            GuildRepository.load(slot=0, testing=True)

        assert True
