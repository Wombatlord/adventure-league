from random import randint, shuffle
from typing import Optional, Iterator
from src.config.constants import guild_names
from src.entities.fighter_factory import EntityPool
from src.entities.entity import Entity
from src.entities.fighter import Fighter
from src.entities.guild import Guild
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

    def defeat(self) -> bool:
        if self.victory() is True:
            # it can't be a defeat if victory is true.
            return False

        if len(eng.guild.team.members) == 0:
            eng.action_queue.append({"message": f"{eng.guild.team.name} defeated!"})

            return True

    def clear_dead_entities(self, entity: Entity):
        try:
            if entity.fighter.is_enemy:
                self.dungeon.enemies.pop(self.dungeon.enemies.index(entity))

            if not entity.fighter.is_enemy:
                self.guild.team.members.pop(self.guild.team.members.index(entity))

        except:
            raise ValueError(f"Could not remove {entity.name=} from array.")

    def process_action_queue(self):
        # new_action_queue = []
        # self._check_action_queue()
        while True:
            try:
                event = self.action_queue.pop(0)

            except IndexError:
                break

            if "message" in event:
                # print("message:", action["message"])
                self.messages.append(event["message"])

            if "dying" in event:
                entity: Entity = event["dying"]

            if "retreat" in event:
                fighter: Fighter = event["retreat"]

                if fighter.owner.is_dead == False:
                    self.guild.team.move_fighter_to_roster(fighter.owner)
                    fighter.retreating = False
  

            if "team triumphant" in event:
                guild: Guild = event["team triumphant"][0]
                dungeon: Dungeon = event["team triumphant"][1]
                guild.claim_rewards(dungeon)

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


def combat_system_run():
    if len(eng.guild.team.members) == 0:
        return
    else:
        eng.dungeon = eng.mission_board.missions[eng.selected_mission]

    # print(f"Initial Room: {eng.dungeon.current_room.enemies}")
    # eng.dungeon.move_to_next_room()
    print(eng.dungeon.rooms)
    
    for i, room in enumerate(eng.dungeon.next_room()):
        print(f"{room.enemies=}")
        while len(room.enemies) > 0:
            print("TURN")
            combat = CombatSystem(eng.guild.team.members, room.enemies)
            turn_actions = combat.iterate_turn()

            for action in turn_actions:
                eng.action_queue.append(action)

            combat_over = False

            if combat.victor() == 0:                
                print(f"2 {room.enemies=}")
                if len(eng.dungeon.rooms[-1].enemies) == 0:
                    eng.action_queue.extend(combat.team_triumphant(eng.guild, eng.dungeon))
                    combat_over = True

            if combat.victor() == 1:
                print(f"2 {eng.guild.team.members=}")
                eng.action_queue.extend(combat.team_defeated(eng.guild.team))
                combat_over = True

            eng.process_action_queue()

            while eng.messages:
                print(eng.messages.pop(0))

            if combat_over:
                break
        if len(eng.guild.team.members) > 0:
            print(eng.guild.team.members)
            print(f"ROOM {i} CLEAR")
        else:
            break
    # If this prints, we have broken the While loop iterating combat rounds and no remaining actions in the action_queue will be processed.
    # Checking action_queue here for sanity, it should be empty.
    print("== COMBAT DONE ==")
    eng._check_action_queue()


class CombatSystem:
    teams: tuple[list[Fighter], list[Fighter]]

    _result: bool | None
    _turn_order: list[Fighter]  # fighter

    def __init__(self, teamA: list[Entity], teamB: list[Entity]) -> None:
        self.teams = (
            [member.fighter for member in teamA],
            [member.fighter for member in teamB],
        )

    def _roll_turn_order(self) -> list:
        actions = []

        combatants = [
            yob for yob in self.teams[0] + self.teams[1] if yob.incapacitated == False
        ]

        battle_size = len(combatants)

        # roll initiatives and sort desc
        initiatives = [*range(0, battle_size)]

        # assing shuffled initatives to combatants
        shuffle(initiatives)
        initiative_roll = zip(combatants, initiatives)
        initiative_roll = sorted(
            initiative_roll, key=lambda item: item[1], reverse=True
        )

        # drop the initiative for the turn order since the index is the battle_size - (initiative + 1)
        self._turn_order = [combatant for combatant, _ in initiative_roll]
        actions.append(
            {
                "message": f"{self._turn_order[0].owner.name.name_and_title} goes first this turn"
            }
        )

        return actions

    def _team_id(self, combatant) -> tuple[int, int]:
        team = 0
        if combatant in self.teams[1]:
            team = 1
        # return team, opposing_team
        return team, (team + 1) % 2

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
                cocombatant
                for cocombatant in self._turn_order
                if (
                    self._team_id(cocombatant)[0] == opposing_team
                    and cocombatant.owner.is_dead is False
                )
            ]
            # print(f"{enemies=}")
            if len(enemies) == 0:
                yield {"message": "the dust has settled, one team is victorious"}
                break

            if combatant.incapacitated == False:
                target_index = combatant.choose_target(enemies)
                target = enemies[target_index]
                actions.extend(combatant.attack(target.owner))
                actions.extend(self._check_for_death(target))
                actions.extend(self._check_for_retreat(combatant))

            while True:
                try:
                    yield actions.pop(0)
                except IndexError:
                    break

        self._turn_order = None

    def _check_for_death(self, target) -> list[dict[str, str]]:
        name = target.owner.name.name_and_title
        results = []
        if target.owner.is_dead:
            print(f"!{name}!: {target.owner.on_death_hooks=}")
            target.owner.die()
            results.append({"dying": target.owner})
            results.append({"message": f"{name} is dead!"})

        return results

    def _check_for_retreat(self, fighter: Fighter) -> list[dict[str, str]]:
        results = []

        if fighter.retreating == True:
            results.append({"retreat": fighter})
            results.append(
                {"message": f"{fighter.owner.name.name_and_title} is retreating!"}
            )

        return results

    def victor(self) -> int | None:
        victor = None
        for team_idx in (0, 1):
            enemies = [
                cocombatant
                for cocombatant in self.teams[(team_idx + 1) % 2]
                if (cocombatant.incapacitated is False)
            ]

            # print(f"{team_idx=}; ", f"{enemies=}")

            if len(enemies) < 1:
                victor = team_idx
                break

        return victor

    def team_triumphant(self, guild, dungeon) -> bool:
        results = []

        message = "\n".join(
            (
                f"{dungeon.boss.name.first_name.capitalize()} is vanquished and the evil within {dungeon.description} is no more!",
                f"{guild.team.name} of the {guild.name} is victorious!",
            )
        )

        results.append({"message": message})
        results.append({"team triumphant": (guild, dungeon)})
        return results

    def team_defeated(self, team) -> bool:
        results = []

        results.append({"message": f"{team.name} defeated!"})

        return results
