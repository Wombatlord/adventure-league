import os
from pathlib import Path

_env = lambda type_, key, default: type_(os.getenv(key, default))

DEBUG = _env(bool, "DEBUG", False)
SAVE_FILE_DIRECTORY = Path("./saves")
TEST_FILE_DIRECTORY = Path("./src/tests/engine/persistence")
