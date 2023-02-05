from src.engine.engine import Engine
from src.engine.describer import Describer

# Instantiate & setup the engine
eng = Engine(describer=Describer())
eng.setup()

# Get some entities in the guild
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
