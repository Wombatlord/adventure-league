import time
from random import randint
from typing import Optional
from src.config.constants import guild_names
from src.entities.fighter_factory import EntityPool, create_random_fighter
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.guild import Guild, Team
from src.entities.dungeon import Dungeon
from src.entities.mission_board import MissionBoard


class Engine:
    dungeon: Dungeon

    def __init__(self) -> None:
        self.guild: Optional[Guild] = None
        self.entity_pool: Optional[EntityPool] = None
        self.dungeon: Optional[Dungeon] = None
        self.mission_board: Optional[MissionBoard] = None
        self.selected_mission = None
        self.messages = []
        self.action_queue = []

    def setup(self) -> None:
        # create a pool of potential recruits
        self.entity_pool = EntityPool(8)
        self.entity_pool.fill_pool()

        # create a guild
        self.guild = Guild(
            name=guild_names[randint(0, len(guild_names) - 1)],
            xp=4000,
            funds=100,
            roster=[],
        )
        self.guild.team.name_team()

        # create a mission board
        self.mission_board = MissionBoard(size=3)
        self.mission_board.fill_board(enemy_amount=3)

    def setup_dungeon(self) -> Dungeon:
        # Prepare a dungeon instance with an enemy / enemies
        fighter = Fighter(hp=30, defence=1, power=3)
        bossName = Name(title="the Terrible", first_name="Tristan", last_name="")
        tristan = Entity(name=bossName, fighter=fighter)
        dungeon = Dungeon(id=0, enemies=[], boss=tristan)
        dungeon.enemies.append(create_random_fighter("goblin"))

        return dungeon

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self):
        print(self.guild.get_dict())
        for entity in self.guild.roster:
            print(entity.get_dict())

    def process_action_queue(self):
        new_action_queue = []
        for action in self.action_queue:
            if "message" in action:
                print(action["message"])
                self.messages.append(action["message"])
                time.sleep(0.75)
        
        self.action_queue = new_action_queue


    def check_action_queue(self):
        for item in self.action_queue:
            print(item)

# Instantiate & setup the engine
eng = Engine()
eng.setup()

# Get some entities in the guild
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)
eng.recruit_entity_to_guild(0)

# eng.guild.team.assign_to_team(
#                         eng.guild.roster, 0
#                     )

# Testing combat interactions between a team and Dungeon enemies

def scripted_run():
    if len(eng.guild.team.members) == 0:
        return
    else:
        eng.dungeon = eng.mission_board.missions[eng.selected_mission]

    while eng.dungeon.boss.is_dead == False:
        for i, merc in enumerate(eng.guild.team.members):

            if not merc.is_dead:
                if len(eng.dungeon.enemies) > 0:
                    
                    eng.action_queue.extend(merc.fighter.attack(eng.dungeon.enemies[0]))

                    if merc.fighter.retreating == True:
                        eng.guild.team.move_to_roster(i)

                if len(eng.dungeon.enemies) == 0 and not eng.dungeon.boss.is_dead:

                    eng.action_queue.extend(merc.fighter.attack(eng.dungeon.boss))
                    
                    if merc.fighter.retreating == True:
                        eng.guild.team.move_to_roster(i)

            if merc.is_dead:
                eng.guild.team.move_to_roster(i)
                eng.guild.remove_from_roster(i)

            eng.dungeon.remove_corpses()

        if len(eng.dungeon.enemies) > 0 and len(eng.guild.team.members) > 0:
            eng.action_queue.extend(eng.dungeon.enemies[0].fighter.attack(eng.guild.team.members[0]))

        if len(eng.dungeon.enemies) == 0 and not eng.dungeon.boss.is_dead:
            if len(eng.guild.team.members) > 0:
                eng.action_queue.extend(eng.dungeon.boss.fighter.attack(eng.guild.team.members[0]))

        # End states & Break.
        if len(eng.dungeon.enemies) == 0 and eng.dungeon.boss.is_dead:
            message = "\n".join(
                (
                    f"{eng.dungeon.boss.name.first_name.capitalize()} is vanquished and the evil within {eng.dungeon.description} is no more!",
                    f"{eng.guild.team.name} of the {eng.guild.name} is victorious!",
                )
            )

            eng.action_queue.append(
                {"message": message}
            )

            print(f"guild claimed: {eng.dungeon.peek_reward()=}")
            eng.guild.claim_rewards(eng.dungeon)

            print(f"peek again: {eng.dungeon.peek_reward()=}")

            break

        if len(eng.guild.team.members) == 0:
            eng.action_queue.append(
                {"message": f"{eng.guild.team.name} defeated!"}
            )
            # print(f"{eng.guild.team.name} defeated!")
            break
