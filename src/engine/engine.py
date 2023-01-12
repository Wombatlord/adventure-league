import time
from random import randint, shuffle
from typing import Optional, Iterator
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

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self):
        print(self.guild.get_dict())
        for entity in self.guild.roster:
            print(entity.get_dict())

    def team_attack_enemies(self, merc) -> None:
        if len(self.dungeon.enemies) > 0:
            self.action_queue.extend(merc.fighter.attack(self.dungeon.enemies[0]))

            if merc.fighter.retreating == True:
                self.action_queue.extend(self.retreat(merc))

    def team_attack_boss(self, merc) -> None:
        if len(self.dungeon.enemies) == 0 and not self.dungeon.boss.is_dead:
            self.action_queue.extend(merc.fighter.attack(self.dungeon.boss))

    def enemies_attack(self) -> None:
        if len(self.dungeon.enemies) > 0 and len(self.guild.team.members) > 0:
            for enemy in self.dungeon.enemies:
                target = enemy.fighter.choose_target(self.guild.team.members)
                    
                self.action_queue.extend(
                        enemy.fighter.attack(self.guild.team.members[target])
                    )
                    
    def boss_attack(self) -> None:
        if len(self.dungeon.enemies) == 0 and not self.dungeon.boss.is_dead:
            if len(self.guild.team.members) > 0:
                self.action_queue.extend(
                        self.dungeon.boss.fighter.attack(self.guild.team.members[0])
                    )

    def retreat(self, target) -> list[dict[str,str]]:
        results = []
        if target in self.guild.team.members:
            results = [{"message": f"{target.name.name_and_title()} is retreating!"}]
            self.guild.team.move_entity_to_roster(target)
        
        return results

    def victory(self) -> bool:
        if len(self.dungeon.enemies) == 0:
            message = "\n".join(
                    (
                        f"{self.dungeon.boss.name.first_name.capitalize()} is vanquished and the evil within {self.dungeon.description} is no more!",
                        f"{self.guild.team.name} of the {self.guild.name} is victorious!",
                    )
                )

            self.action_queue.append({"message": message})

            print(f"guild claimed: {self.dungeon.peek_reward()=}")
            self.guild.claim_rewards(self.dungeon)

            print(f"peek again: {self.dungeon.peek_reward()=}")


            return True
    
    def defeat(self) -> bool:
        if self.victory() is True:
            # it can't be a defeat if victory is true.
            return False

        if len(eng.guild.team.members) == 0:
            eng.action_queue.append({"message": f"{eng.guild.team.name} defeated!"})

            return True

    def process_action_queue(self):
        # new_action_queue = []
        # self._check_action_queue()
        while True:
            try:
                action = self.action_queue.pop(0)

            except IndexError:
                break
            
            if "message" in action:
                # print("message:", action["message"])
                self.messages.append(action["message"])

            if "dying" in action:
                target = action["dying"]
                # new_actions = self.dying(target)
                
                
                # self.action_queue.extend(new_actions)

                # Remove any dead entities from their respective arrays.
                self.guild.team.remove_corpses()
                self.dungeon.remove_corpses()
                print("DYING ACTION EXTEND")

            if "retreat" in action:
                target = action["retreat"]
                new_actions = self.retreat(target)

                self.action_queue.extend(new_actions)

    def _check_action_queue(self):
        for item in self.action_queue:
            print(f"item: {item}")


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
        for merc in eng.guild.team.members:
            if not merc.is_dead:
                eng.team_attack_enemies(merc)

                eng.team_attack_boss(merc)
                eng.process_action_queue()
            
            eng.dungeon.remove_corpses()

        # ENEMY ATTACKS
        eng.enemies_attack()
        
        # BOSS ATTACK
        eng.boss_attack()
        eng.process_action_queue()

        # End states & Break.    
        if eng.victory() or eng.defeat():
            eng.process_action_queue()
            break


def combat_system_run():
    if len(eng.guild.team.members) == 0:
        return
    else:
        eng.dungeon = eng.mission_board.missions[eng.selected_mission]

    while len(eng.dungeon.enemies) > 0:
        print("TURN")
        combat = CombatSystem(eng.guild.team.members, eng.dungeon.enemies)
        turn_actions = combat.iterate_turn()
       
            
        for action in turn_actions:
            eng.action_queue.append(action)
        
        combat_over = False
        print(f"{combat.victor()=}")
        if combat.victor() == 0:
            eng.action_queue.append({"message": "you win"})
            combat_over = True
            eng.guild.claim_rewards(eng.dungeon)
            
        if combat.victor() == 1:
            eng.action_queue.append({"message": "goblins win"})
            combat_over = True
            
    
        eng.process_action_queue()
        
        while eng.messages:
            print(eng.messages.pop(0))

        if combat_over:
            break

    # If this prints, we have broken the While loop iterating combat rounds and no remaining actions in the action_queue will be processed.
    # Checking action_queue here for sanity, it should be empty.
    print("== COMBAT DONE ==")
    eng._check_action_queue()
        
class CombatSystem:
    teams: tuple[list[Fighter], list[Fighter]]
    
    _result: bool | None
    _turn_order: list[
        Fighter # fighter
    ]

    def __init__(self, teamA: list[Entity], teamB: list[Entity]) -> None:
        self.teams = (
            [member.fighter for member in teamA], 
            [member.fighter for member in teamB]
        )

    def _roll_turn_order(self) -> list:
        actions = []
        
        combatants = [yob for yob in self.teams[0] + self.teams[1] if yob.incapacitated == False]

        battle_size = len(combatants)
        
        # roll initiatives and sort desc
        initiatives = [*range(0, battle_size)]
        
        # assing shuffled initatives to combatants
        shuffle(initiatives)
        initiative_roll = zip(combatants, initiatives)
        initiative_roll = sorted(
            initiative_roll,
            key=lambda item: item[1],
            reverse=True
        )

        # drop the initiative for the turn order since the index is the battle_size - (initiative + 1)
        self._turn_order = [
            combatant for combatant, _ in initiative_roll
        ]
        actions.append({"message": f"{self._turn_order[0].owner.name.name_and_title} goes first this turn"})
        
        return actions

    def _team_id(self, combatant) -> tuple[int, int]:
        team = 0
        if combatant in self.teams[1]:
            team = 1
        # return team, opposing_team
        return team, (team  + 1) % 2

    def iterate_turn(self) -> Iterator[dict[str, str]]:
        actions = self._roll_turn_order()

        while True:
            try:
                yield actions.pop(0)
            except IndexError:
                break

        for combatant in self._turn_order:
            _, opposing_team = self._team_id(combatant)
            
            enemies = [
                cocombatant for cocombatant in self._turn_order 
                if (
                    self._team_id(cocombatant)[0] == opposing_team 
                    and cocombatant.incapacitated is False
                )
            ]

            if len(enemies) == 0:
                yield {"message": "the dust has settled, one team is victorious"}
                break
            
            if combatant.incapacitated == False:
                target_index = combatant.choose_target(enemies)
                target = enemies[target_index]
                actions.extend(combatant.attack(target.owner))
                actions.extend(self.death_check(target))
            
            while True:
                try:
                    yield actions.pop(0)
                except IndexError:
                    break

        self._turn_order = None

    def death_check(self, target) -> list[dict[str, str]]:
        name = target.owner.name.name_and_title
        results = []
        if target.owner.is_dead:
            results.append(
                {"dying": target.owner}
            )
            results.append({"message": f"{name} is dead!"})
            
        print(f"dying func: {results}")
        return results

    def victor(self) -> int | None:
        victor = None
        for team_idx in (0, 1):
            enemies = [
                cocombatant for cocombatant in self.teams[(team_idx +1) % 2]
                if (
                    cocombatant.incapacitated is False
                )
            ]

            print(f"{team_idx=}; ", f"{enemies=}")

            if len(enemies) < 1:
                victor = team_idx
                break

        return victor
