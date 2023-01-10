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

    def dying(self, target):
        name = target.name.name_and_title()
        if target in self.guild.team.members:
            results = [{"message": f"{name} is dead!"}]
            self.guild.team.members.pop(self.guild.team.members.index(target))
        else:
            results = [{"message": f"{name} is dead!"}]

        return results

    def retreat(self, target):
        results = []
        if target.fighter.retreating == True:
            results = [{"retreat": target}]

        return results

    def process_action_queue(self):
        new_action_queue = []
        # self._check_action_queue()
        for action in self.action_queue:
            if "message" in action:
                print(action["message"])
                self.messages.append(action["message"])

            if "dying" in action:
                target = action["dying"]
                new_actions = self.dying(target)
                
                if new_actions:
                    new_action_queue.extend(new_actions)

            if "retreat" in action:
                target = action["retreat"]
                eng.guild.team.move_entity_to_roster(target)
        
        self.action_queue = new_action_queue

    def _check_action_queue(self):
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
        # TEAM MEMBER ATTACKS
        for i, merc in enumerate(eng.guild.team.members):
            if not merc.is_dead:
                if len(eng.dungeon.enemies) > 0:

                    eng.action_queue.extend(merc.fighter.attack(eng.dungeon.enemies[0]))

                    if merc.fighter.retreating == True:
                        eng.action_queue.extend(eng.retreat(merc))

                    eng.process_action_queue()

                if len(eng.dungeon.enemies) == 0 and not eng.dungeon.boss.is_dead:

                    eng.action_queue.extend(merc.fighter.attack(eng.dungeon.boss))

                    if eng.dungeon.boss.is_dead:
                        eng.action_queue.extend(eng.dying(eng.dungeon.boss))
                    eng.process_action_queue()
            
            eng.dungeon.remove_corpses()

        # ENEMY ATTACKS
        if len(eng.dungeon.enemies) > 0 and len(eng.guild.team.members) > 0:
            for enemy in eng.dungeon.enemies:
                target = enemy.fighter.choose_target(eng.guild.team.members)
                
                eng.action_queue.extend(
                    enemy.fighter.attack(eng.guild.team.members[target])
                )

                # eng.action_queue.extend(
                #     eng.dungeon.enemies[0].fighter.attack(eng.guild.team.members[0])
                # )
                eng.process_action_queue()
        
        # BOSS ATTACK
        if len(eng.dungeon.enemies) == 0 and not eng.dungeon.boss.is_dead:
            if len(eng.guild.team.members) > 0:
                eng.action_queue.extend(
                    eng.dungeon.boss.fighter.attack(eng.guild.team.members[0])
                )
                eng.process_action_queue()

        # End states & Break.
        if len(eng.dungeon.enemies) == 0 and eng.dungeon.boss.is_dead:
            message = "\n".join(
                (
                    f"{eng.dungeon.boss.name.first_name.capitalize()} is vanquished and the evil within {eng.dungeon.description} is no more!",
                    f"{eng.guild.team.name} of the {eng.guild.name} is victorious!",
                )
            )

            eng.action_queue.append({"message": message})

            print(f"guild claimed: {eng.dungeon.peek_reward()=}")
            eng.guild.claim_rewards(eng.dungeon)

            print(f"peek again: {eng.dungeon.peek_reward()=}")
            eng.process_action_queue()

            break

        if len(eng.guild.team.members) == 0:
            eng.action_queue.append({"message": f"{eng.guild.team.name} defeated!"})
            eng.process_action_queue()
            break
