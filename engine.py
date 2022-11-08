from typing import Optional
from src.entities.fighter_factory import EntityPool
from src.entities.entity import Entity
from src.entities.fighter import Fighter
from src.entities.guild import Guild


class Dungeon:
    def __init__(self, enemies: list[Entity] = []) -> None:
        self.enemies: Optional[list[Entity]] = enemies
        self.treasure = None

    def remove_corpses(self):
        # Iterate through enemies and remove dead enemies from the array.
        for i, enemy in enumerate(self.enemies):
            if enemy.is_dead:
                self.enemies.pop(i)


class Engine:
    def __init__(self) -> None:
        self.guild: Optional[Guild] = None
        self.entity_pool: Optional[EntityPool] = None
        self.dungeon: Optional[Dungeon] = None

    def setup(self) -> None:
        # create a pool of potential recruits
        self.entity_pool = EntityPool(5)
        self.entity_pool.fill_pool()

        # create a guild
        self.guild = Guild(name=None, level=4, funds=100, roster=[])

        # prepare a dungeon
        self.dungeon = self.setup_dungeon()

    def setup_dungeon(self) -> Dungeon:
        # Prepare a dungeon instance with an enemy / enemies
        fighter = Fighter(hp=10, defence=2, power=4)
        enemy = Entity(name="Tristan the Terrible", fighter=fighter)
        dungeon = Dungeon()
        dungeon.enemies.append(enemy)

        return dungeon

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self):
        # print(self.guild)
        print(self.guild.name)
        for entity in self.guild.roster:
            print(entity.get_dict())

    def test_attack(self):
        f1 = Fighter(5, 1, 3, 1)
        f2 = Fighter(5, 1, 3, 1)

        en1 = Entity(
            "EN1",
            0,
            fighter=f1,
        )

        en2 = Entity("EN2", 0, fighter=f2)

        en1.fighter.attack(en2)
        en2.fighter.attack(en1)


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
                print(f"{merc.name.capitalize()} retreats!")
                eng.guild.team.remove_from_team(i)
        
        if merc.is_dead:
            eng.guild.team.remove_from_team(i)
            # print(eng.guild.team)

        eng.dungeon.remove_corpses()

    if len(eng.dungeon.enemies) > 0 and len(eng.guild.team.members) > 0:
        eng.dungeon.enemies[0].fighter.attack(eng.guild.team.members[0])

    if len(eng.guild.team.members) == 0:
        print(f"{eng.guild.team.name} defeated!")
        break

eng.print_guild()

# eng.recruit_entity_to_guild(1)
# eng.guild.roster[0].fighter.attack(eng.guild.roster[1])
