from typing import Optional
from src.entities.fighter_factory import EntityPool
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.guild import Guild
from src.entities.dungeon import Dungeon
from src.entities.mission_board import MissionBoard

class Engine:
    def __init__(self) -> None:
        self.guild: Optional[Guild] = None
        self.entity_pool: Optional[EntityPool] = None
        self.dungeon: Optional[Dungeon] = None
        self.mission_board: Optional[MissionBoard] = None

    def setup(self) -> None:
        # create a pool of potential recruits
        self.entity_pool = EntityPool(5)
        self.entity_pool.fill_pool()

        # create a guild
        self.guild = Guild(name=None, level=4, funds=100, roster=[])

        # create a mission board
        self.mission_board = MissionBoard(size=3)
        self.mission_board.fill_board(enemy_amount=3)
        
        # prepare a dungeon
        self.dungeon = self.setup_dungeon()

    def setup_dungeon(self) -> Dungeon:
        # Prepare a dungeon instance with an enemy / enemies
        fighter = Fighter(hp=30, defence=1, power=3)
        tristan = Name(title="the Terrible", first_name="Tristan", last_name="")
        enemy = Entity(name=tristan, fighter=fighter)
        dungeon = Dungeon(id=0, enemies=[])
        dungeon.enemies.append(enemy)

        return dungeon

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self):
        # print(self.guild)
        print(self.guild.get_dict())
        for entity in self.guild.roster:
            print(entity.get_dict())


# Instantiate & setup the engine
eng = Engine()
eng.setup()
# eng.test_attack()


# Get some entities in the guild
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(1)

# Assign entities to a team within the guild
eng.guild.team.assign_to_team(eng.guild.roster, 0)
eng.guild.team.assign_to_team(eng.guild.roster, 1)
print(eng.guild.team.name)

# Testing combat interactions between a team and Dungeon enemies
while len(eng.dungeon.enemies) > 0:
    for i, merc in enumerate(eng.guild.team.members):
        
        if not merc.is_dead and len(eng.dungeon.enemies) > 0:
            a = merc.fighter.attack(eng.dungeon.enemies[0])
            
            if a == 0:
                print(f"{merc.name.first_name.capitalize()} retreats!")
                eng.guild.team.remove_from_team(i)
        
        if merc.is_dead:
            eng.guild.team.remove_from_team(i)
            eng.guild.remove_from_roster(i)
            # print(eng.guild.team)

        eng.dungeon.remove_corpses()

    if len(eng.dungeon.enemies) > 0 and len(eng.guild.team.members) > 0:
        eng.dungeon.enemies[0].fighter.attack(eng.guild.team.members[0])

    if len(eng.guild.team.members) == 0:
        print(f"{eng.guild.team.name} defeated!")
        break

eng.print_guild()
print(eng.mission_board.missions[0].id)
print(eng.mission_board.missions[1].enemies[0].name.first_name.capitalize())

# eng.recruit_entity_to_guild(1)
# eng.guild.roster[0].fighter.attack(eng.guild.roster[1])
