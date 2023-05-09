from src.engine.engine import Engine

# Instantiate & setup the engine

_eng: Engine | None = None


def _bootstrap():
    global _eng
    _eng = Engine()


def _get_eng() -> Engine:
    global _eng
    if _eng is not None:
        return _eng

    _bootstrap()
    return _eng


eng = _get_eng()
