import os

_env = lambda type_, key, default: type_(os.getenv(key, default))

DEBUG = _env(bool, "DEBUG", False)
