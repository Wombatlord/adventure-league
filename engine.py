from typing import Optional
from entities.fighter_factory import EntityPool
from src.entities.guild import Guild


class Engine:
    def __init__(self) -> None:
        self.guild: Optional[Guild] = None
        self.entity_pool: Optional[EntityPool] = None

    def setup(self):
        self.entity_pool = EntityPool(5)
        self.entity_pool.fill_pool()
        # create a guild
        self.guild = Guild(name="GUILD", level=1, funds=0, roster=[])
        self.guild.recruit(1, self.entity_pool.pool)

    def print_guild(self):
        print(self.guild)
        print(self.guild.name)
        for entity in self.guild.roster:
            print(entity.fighter.defence)
        


eng = Engine()

eng.setup()
eng.print_guild()
