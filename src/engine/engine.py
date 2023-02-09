from __future__ import annotations
from random import randint
from typing import Optional, Generator, Any, NamedTuple
from src.config.constants import guild_names
from src.entities.fighter_factory import EntityPool
from src.entities.entity import Entity
from src.entities.fighter import Fighter
from src.entities.guild import Guild
from src.entities.dungeon import Dungeon
from src.entities.mission_board import MissionBoard
from src.projection import health
from src.systems.combat import CombatRound
from src.engine.describer import Describer

class MessagesWithAlphas(NamedTuple):
    messages: list[str]
    alphas: list[int]


Action = dict[str, Any]
Turn = Generator[None, None, Action]  # <-
Round = Generator[None, None, Turn]  # <- These are internal to the combat system
Encounter = Generator[None, None, Round]
Quest = Generator[None, None, Encounter]

projections = {"entity_data": [health]}


def flush_all() -> None:
    for subscribers in projections.values():
        for subscriber in subscribers:
            subscriber.flush()


class Engine:
    game_state: GameState
    default_clock_value = 0.5
    
    def __init__(self) -> None:
        self.action_queue: list[Action] = []
        self.messages: list[str] = []
        self.combat: Generator[None, None, Action]
        self.awaiting_input: bool = False
        self.message_alphas: list[int] = []
        self.alpha_max: int = 255
        self.chosen_target: int | None = None
        self.update_clock = self.default_clock_value
        self.selected_mission: int | None = None
        self.mission_in_progress: bool = False

    def setup(self) -> None:
        self.game_state = GameState()
        # create a pool of potential recruits
        pool = EntityPool(15)
        pool.fill_pool()
        self.game_state.set_entity_pool(pool)

        # create a guild
        guild = Guild(
            name=guild_names[randint(0, len(guild_names) - 1)],
            xp=4000,
            funds=100,
            roster=[],
        )
        guild.team.name_team()
        self.game_state.set_guild(guild)

        # create a mission board
        mission_board = MissionBoard(size=3)
        mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
        self.game_state.set_mission_board(mission_board)
        flush_all()

    def recruit_entity_to_guild(self, selection_id) -> None:
        guild = self.game_state.get_guild()
        entity_pool = self.game_state.get_entity_pool()
        guild.recruit(selection_id, entity_pool.pool)

    def process_action_queue(self) -> None:
        # new_action_queue = []
        # self._check_action_queue()
        while True:
            try:
                event = self.action_queue.pop(0)

            except IndexError:
                break

            self.process_one(event)

    def process_one(self, event: Action) -> None:
        if "message" in event:
            # print("message:", action["message"])
            self.messages.append(event["message"])

        if "await target" in event:
            fighter = event["await target"]
            self.await_input()

        to_project = {*event.keys()} & {*projections.keys()}
        for key in to_project:
            for projection in projections[key]:
                projection.consume(action=event)

        if "delay" in event:
            delay = event["delay"]
            self.increase_update_clock_by_delay(delay)

        if "dying" in event:
            entity: Entity = event["dying"]

        if "retreat" in event:
            fighter: Fighter = event["retreat"]

            if fighter.owner.is_dead == False:
                self.game_state.guild.team.move_fighter_to_roster(fighter.owner)

        if "team triumphant" in event:
            guild: Guild = event["team triumphant"][0]
            dungeon: Dungeon = event["team triumphant"][1]
            dungeon.cleared = True
            guild.claim_rewards(dungeon)

    def _check_action_queue(self) -> None:
        for item in self.action_queue:
            print(f"item: {item}")
    
    def reset_update_clock(self):
        self.update_clock = self.default_clock_value
    
    def increase_update_clock_by_delay(self, delay):
        self.update_clock += delay

    def last_n_messages(self, n: int) -> list[str]:
        return self.messages[-n:]

    def last_n_messages_with_alphas(self, n: int) -> MessagesWithAlphas:
        if (
            len(self.message_alphas) < len(self.messages)
            and len(self.message_alphas) < n
        ):
            self.message_alphas.insert(0, self.alpha_max)
            self.alpha_max -= 50

        return MessagesWithAlphas(self.messages[-n:], self.message_alphas)

    def await_input(self) -> None:
        self.awaiting_input = True

    def set_target(self, target_choice) -> None:
        self.chosen_target = target_choice

    def end_of_combat(self, win: bool = True) -> list[Action]:
        guild = self.game_state.get_guild()
        dungeon = self.game_state.get_dungeon()
        
        if win:
            actions = self.team_triumphant_actions(guild, dungeon)
            self.game_state.guild.claim_rewards(dungeon)
        else:
            actions = self.team_defeated(guild.team)

        self.game_state.dungeon = None
        self.mission_in_progress = False
        return actions

    def init_dungeon(self) -> None:
        mission_board = self.game_state.get_mission_board()
        self.game_state.set_dungeon(mission_board.missions[self.selected_mission])
        
        # self.game_state.dungeon = self.game_state.mission_board.missions[self.selected_mission]

    def init_combat(self) -> None:
        self.mission_in_progress = True
        self.messages = []
        self.message_alphas = []
        self.alpha_max = 255
        flush_all()
        self.combat = self._generate_combat_actions()

    def initial_health_values(self, team, enemies) -> list[Action]:
        result = []

        for combatant in team:
            result.append(combatant.annotate_event({}))

        for combatant in enemies:
            result.append(combatant.annotate_event({}))

        return result

    def next_combat_action(self) -> bool:
        """
        This is the source ==Action==> consumer connection
        """
        try:
            action = next(self.combat)
            self.process_one(action)
            return True
        except StopIteration:
            return False

    def _generate_combat_actions(self) -> Generator[None, None, Action]:
        quest = self.game_state.dungeon.room_generator()
        
        yield {
            "message": Describer.describe_entrance(self),
            "delay": 3
        }

        for encounter in quest:

            healths = self.initial_health_values(
                self.game_state.guild.team.members, encounter.enemies
            )

            for h in healths:
                yield h

            while encounter.enemies and self.game_state.guild.team.members:
                # Beginning of encounter actions/state changes go here
                combat_round = CombatRound(
                    self.game_state.guild.team.members, encounter.enemies, self.await_input
                )

                # example of per-round actions
                for action in combat_round.initiative_roll_actions:
                    yield action

                # then we begin iterating turns
                while combat_round.continues():
                    if self.awaiting_input == False:
                        # The following will attempt to yield attack actions for the fighter at the beginning of the combat_round._turn_order.
                        # If that fighter is a player merc, it will skip attacking and instead cause self.awaiting_input to be true
                        # via the combatants request_target() method.
                        actions = combat_round.single_fighter_turn()

                    while self.awaiting_input == True:
                        # We sit in this loop until eng.chosen_target is updated by user input
                        # Once the user inputs a valid target and causes the next iteration,
                        # attack actions will be yielded and awaiting_input will become false.
                        actions = combat_round.player_fighter_turn(self.chosen_target)

                        # Yield one of the following depending on if the user has selected a target
                        # Reset the target after a loop ending run of player_fighter_turn
                        if self.chosen_target is None:
                            yield {
                                "message": "Use the numpad to choose a target before advancing!"
                            }
                        else:
                            self.chosen_target = None
                            yield {}

                    for action in actions:
                        yield action

            if len(self.game_state.guild.team.members) == 0:
                break

            if not self.game_state.dungeon.boss.is_dead:
                yield {
                    "message": Describer.describe_room_complete(self),
                    "delay": 3
                }

        if combat_round.victor() == 0:
            win = True
        else:
            win = False

        for action in self.end_of_combat(win=win):
            yield action

    @staticmethod
    def team_triumphant_actions(guild, dungeon) -> list[Action]:
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

    @staticmethod
    def team_defeated(team) -> bool:
        results = []

        results.append({"message": f"{team.name} defeated!"})

        return results


class GameState:
    guild: Optional[Guild] = None
    entity_pool: Optional[EntityPool] = None
    dungeon: Optional[Dungeon] = None
    mission_board: Optional[MissionBoard] = None
        
    def get_guild(self):
        return self.guild
    
    def get_entity_pool(self):
        return self.entity_pool
    
    def get_dungeon(self):
        return self.dungeon
    
    def get_mission_board(self):
        return self.mission_board
    
    def set_guild(self, guild):
        self.guild = guild
    
    def set_entity_pool(self, pool):
        self.entity_pool = pool
    
    def set_dungeon(self, dungeon):
        self.dungeon = dungeon

    def set_mission_board(self, board):
        self.mission_board = board