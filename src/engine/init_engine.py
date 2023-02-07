from src.engine.engine import Engine

# Instantiate & setup the engine

_eng: Engine | None = None

def _bootstrap():
    global _eng    
    _eng = Engine()
    _eng.setup()

    # Get some entities in the guild
    _eng.recruit_entity_to_guild(0)
    _eng.recruit_entity_to_guild(0)
    _eng.recruit_entity_to_guild(0)
    
def _get_eng() -> Engine:
    global _eng
    if _eng is not None:
        return _eng
    
    _bootstrap()
    return _eng

eng = _get_eng()