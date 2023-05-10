from __future__ import annotations

from typing import Any, Callable, Generator, NamedTuple

from pyglet.math import Vec2

from src import config
from src.engine.describer import Describer
from src.engine.dispatcher import StaticDispatcher, VolatileDispatcher
from src.engine.game_state import AwardSpoilsHandler, GameState
from src.engine.mission_board import MissionBoard
from src.engine.persistence.game_state_repository import GuildRepository
from src.entities.combat.fighter_factory import RecruitmentPool
from src.systems.combat import CombatRound


class MessagesWithAlphas(NamedTuple):
    messages: list[str]
    alphas: list[int]


Event = dict[str, Any]
Turn = Generator[None, None, Event]  # <-
Round = Generator[None, None, Turn]  # <- These are internal to the combat system
Encounter = Generator[None, None, Round]
Quest = Generator[None, None, Encounter]


Handler = Callable[[dict], None]


class Engine:
    game_state: GameState
    default_clock_value = 0.3
    guild_repository = GuildRepository

    def __init__(self) -> None:
        self.event_queue: list[Event] = []
        self.messages: list[str] = []
        self.combat: Generator[None, None, Event]
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
        from src.engine import static_subscribers

        static_subscribers.subscribe(self)

    def static_subscribe(self, topic: str, handler_id: str, handler: Handler):
        self.projection_dispatcher.subscribe(topic, handler_id, handler)

    def subscribe(self, topic: str, handler_id: str, handler: Handler):
        self.combat_dispatcher.subscribe(topic, handler_id, handler)

    def new_game(self) -> None:
        self.game_state = GameState(self)
        self.static_subscribe(
            topic="team triumphant",
            handler_id="game_state",
            handler=AwardSpoilsHandler(self.game_state).handle,
        )
        # create a pool of potential recruits
        pool = RecruitmentPool(15)
        pool.fill_pool()
        self.game_state.set_entity_pool(pool)
        self.game_state.setup()
        self.game_state.guild.team.name_team()
        self.game_state.set_team()

        # Get some entities in the guild
        self.recruit_entity_to_guild(0)
        self.recruit_entity_to_guild(0)
        self.recruit_entity_to_guild(0)

    def load_save_slot(self, slot: int):
        self.game_state = GameState(self)
        self.static_subscribe(
            topic="team triumphant",
            handler_id="game_state",
            handler=AwardSpoilsHandler(self.game_state).handle,
        )
        self.game_state.guild = self.guild_repository.load(slot)
        self.game_state.set_team()
        pool = RecruitmentPool(15 - self.game_state.guild.current_roster_count)
        pool.fill_pool()
        self.game_state.set_entity_pool(pool)

    def save_to_slot(self, slot: int):
        self.guild_repository.save(slot, self.game_state.guild)

    def get_save_slot_metadata(self) -> list[dict]:
        return self.guild_repository.get_slot_info()

    def flush_all(self):
        self.flush_subscriptions()
        self.flush_projections()
        for entity in self.game_state.entities():
            entity.clear_hooks()

    def flush_subscriptions(self):
        self.combat_dispatcher.flush_subs()

    def flush_projections(self):
        self.projection_dispatcher.publish({"flush": None})

    def recruit_entity_to_guild(self, selection_id) -> None:
        guild = self.game_state.get_guild()
        entity_pool = self.game_state.get_entity_pool()
        guild.recruit(selection_id, entity_pool.pool)

    def process_event_queue(self) -> None:
        while True:
            try:
                event = self.event_queue.pop(0)

            except IndexError:
                break

            self.process_one(event)

    def _set_target(self, target: int) -> bool:
        try:
            self.set_target(target)
            return True
        except Exception as e:
            print(f"SOURCE: {__file__}; ERROR: Failed to select target with error: {e}")
            return False

    def process_one(self, event: Event) -> None:
        if "cleanup" in event:
            self.flush_all()
            return

        if "delay" in event:
            # Purely an instruction to the engine
            self._handle_delay_event(event)
            del event["delay"]

        if "message" in event:
            self.messages.append(event["message"])

        if config.DEBUG:
            print(f"{event=}")

        self.projection_dispatcher.publish(event)
        self.combat_dispatcher.publish(event)

    def _handle_delay_event(self, event):
        self.increase_update_clock_by_delay(event.get("delay", 0))

    def reset_update_clock(self):
        self.update_clock = self.default_clock_value

    def increase_update_clock_by_delay(self, delay):
        self.update_clock += delay

    def await_input(self) -> None:
        self.awaiting_input = True

    def input_received(self) -> None:
        self.awaiting_input = False

    def set_target(self, target_choice) -> None:
        self.chosen_target = target_choice
        self.next_combat_event()
        self.awaiting_input = False

    def end_of_combat(self, win: bool = True) -> list[Event]:
        guild = self.game_state.get_guild()
        dungeon = self.game_state.get_dungeon()

        if win:
            events = self.team_triumphant_events(guild, dungeon)
            self.game_state.guild.claim_rewards(dungeon)
        else:
            events = self.team_defeated(guild.team)

        self.game_state.dungeon = None
        self.mission_in_progress = False
        return events

    def init_dungeon(self) -> None:
        mission_board = self.game_state.get_mission_board()
        self.game_state.set_dungeon(mission_board.missions[self.selected_mission])

    def init_combat(self) -> None:
        self.mission_in_progress = True
        self.messages = []
        self.message_alphas = []
        self.alpha_max = 255
        self.combat = self._generate_combat_events()

    def initial_health_values(self, team, enemies) -> list[Event]:
        result = []

        for combatant in team:
            result.append(combatant.annotate_event({}))

        for combatant in enemies:
            result.append(combatant.annotate_event({}))

        return result

    def grid_offset(self, x: int, y: int, constant_scale, grid_aspect, w, h) -> Vec2:
        return Vec2(
            (x - y) * grid_aspect[0],
            (x + y) * grid_aspect[1],
        ) * constant_scale + Vec2(w / 2, 7 * h / 8)

    def next_combat_event(self) -> bool:
        """
        This is the source ==Event==> consumer connection
        """
        try:
            event = next(self.combat)
            self.process_one(event)
            return True
        except StopIteration:
            return False

    def _generate_combat_events(self) -> Generator[Event, None, None]:
        quest = self.game_state.dungeon.room_generator()

        yield {"message": Describer.describe_entrance(self), "delay": 3}

        combat_round = None
        for encounter in quest:
            encounter.include_party(self.game_state.team.members)
            yield {"new_encounter": encounter}

            yield from self.initial_health_values(
                self.game_state.team.members, encounter.enemies
            )

            while encounter.enemies and self.game_state.guild.team.members:
                # Beginning of encounter events/state changes go here
                combat_round = CombatRound(
                    self.game_state.guild.team.members,
                    encounter.enemies,
                )

                # example of per-round events
                yield from combat_round.initiative_roll_events

                # then we begin iterating turns
                while combat_round.continues():
                    yield from combat_round.do_turn()

            if len(self.game_state.guild.team.members) == 0:
                break

            if not self.game_state.dungeon.boss.is_dead:
                yield {"message": Describer.describe_room_complete(self), "delay": 3}

        if combat_round and combat_round.victor() == 0:
            win = True
        else:
            win = False

        yield from self.end_of_combat(win=win)

        yield {"cleanup": encounter}

    @staticmethod
    def team_triumphant_events(guild, dungeon) -> list[Event]:
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
    def team_defeated(team) -> list[Event]:
        results = []

        results.append({"message": f"{team.name} defeated!"})

        return results

    def refresh_mission_board(self):
        if self.game_state.mission_board is None:
            return

        self.game_state.mission_board.clear_board()
        self.game_state.mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
