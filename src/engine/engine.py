from __future__ import annotations

import weakref
from random import randint
from typing import Any, Callable, Generator, NamedTuple, Optional

from src.config.constants import guild_names
from src.engine.describer import Describer
from src.engine.dispatcher import StaticDispatcher, VolatileDispatcher
from src.engine.game_state import AwardSpoilsHandler, GameState
from src.entities.dungeon import Dungeon
from src.entities.entity import Entity
from src.entities.fighter import Fighter
from src.entities.fighter_factory import EntityPool
from src.entities.guild import Guild, Team
from src.entities.mission_board import MissionBoard
from src.projection import health
from src.systems.combat import CombatRound


class MessagesWithAlphas(NamedTuple):
    messages: list[str]
    alphas: list[int]


Action = dict[str, Any]
Turn = Generator[None, None, Action]  # <-
Round = Generator[None, None, Turn]  # <- These are internal to the combat system
Encounter = Generator[None, None, Round]
Quest = Generator[None, None, Encounter]

projections = {"entity_data": [health]}


Handler = Callable[[dict], None]


class Engine:
    game_state: GameState
    default_clock_value = 0.3

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
        self.current_room = None
        self.subscriptions: dict[str, dict[str, Handler]] = {}
        self.combat_dispatcher = VolatileDispatcher(self)
        self.projection_dispatcher = StaticDispatcher(self)
        self.projection_dispatcher.static_subscribe(
            topic="entity_data",
            handler_id="health_projection",
            handler=health.consume,
        )
        self.projection_dispatcher.static_subscribe(
            topic="flush",
            handler_id="health_projection",
            handler=health.flush_handler,
        )

    def subscribe(self, topic: str, handler_id: str, handler: Handler):
        self.combat_dispatcher.subscribe(topic, handler_id, handler)

    def setup(self) -> None:
        self.game_state = GameState()
        self.projection_dispatcher.static_subscribe(
            topic="team triumphant",
            handler_id="game_state",
            handler=AwardSpoilsHandler(self.game_state).handle,
        )
        # create a pool of potential recruits
        pool = EntityPool(15)
        pool.fill_pool()
        self.game_state.set_entity_pool(pool)
        self.game_state.setup()
        self.game_state.guild.team.name_team()
        self.game_state.set_team()

        # create a mission board
        mission_board = MissionBoard(size=3)
        mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
        self.game_state.set_mission_board(mission_board)
        self.flush_all()

    def flush_all(self):
        self.flush_subscriptions()
        self.flush_projections()

    def flush_subscriptions(self):
        self.combat_dispatcher.flush_subs()

    def flush_projections(self):
        self.projection_dispatcher.publish({"flush": None})

    def recruit_entity_to_guild(self, selection_id) -> None:
        guild = self.game_state.get_guild()
        entity_pool = self.game_state.get_entity_pool()
        guild.recruit(selection_id, entity_pool.pool)

    def process_action_queue(self) -> None:
        while True:
            try:
                event = self.action_queue.pop(0)

            except IndexError:
                break

            self.process_one(event)

    def process_one(self, event: Action) -> None:
        if "cleanup" in event:
            self.flush_all()
            return

        if "delay" in event:
            # Purely an instruction to the engine
            self._handle_delay_action(event)
            del event["delay"]

        if "await_input" in event:
            self.await_input()
            del event["await_input"]

        if "message" in event:
            self.messages.append(event["message"])

        self.projection_dispatcher.publish(event)
        self.combat_dispatcher.publish(event)

    def _handle_delay_action(self, event):
        self.increase_update_clock_by_delay(event.get("delay", 0))

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

    def init_combat(self) -> None:
        self.mission_in_progress = True
        self.messages = []
        self.message_alphas = []
        self.alpha_max = 255
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

        yield {"message": Describer.describe_entrance(self), "delay": 3}

        for encounter in quest:
            encounter.include_party(self.game_state.team.members)
            yield {"new_encounter": encounter}

            healths = self.initial_health_values(
                self.game_state.team.members, encounter.enemies
            )

            for h in healths:
                yield h

            while encounter.enemies and self.game_state.guild.team.members:
                # Beginning of encounter actions/state changes go here
                combat_round = CombatRound(
                    self.game_state.guild.team.members,
                    encounter.enemies,
                    self.await_input,
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
                yield {"message": Describer.describe_room_complete(self), "delay": 3}

        if combat_round.victor() == 0:
            win = True
        else:
            win = False

        for action in self.end_of_combat(win=win):
            yield action

        yield {"cleanup": encounter}

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
        results.append({"team triumphant": {"dungeon": dungeon}})
        return results

    @staticmethod
    def team_defeated(team) -> list[Action]:
        results = []

        results.append({"message": f"{team.name} defeated!"})

        return results

    def refresh_mission_board(self):
        if self.game_state.mission_board is None:
            return

        self.game_state.mission_board.clear_board()
        self.game_state.mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
