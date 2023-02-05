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
    def __init__(self, describer) -> None:
        self.guild: Optional[Guild] = None
        self.entity_pool: Optional[EntityPool] = None
        self.dungeon: Optional[Dungeon] = None
        self.mission_board: Optional[MissionBoard] = None
        self.mission_in_progress: bool = False
        self.selected_mission: int | None = None
        self.messages: list[str] = []
        self.action_queue: list[Action] = []
        self.combat: Generator[None, None, Action]
        self.awaiting_input: bool = False
        self.message_alphas: list[int] = []
        self.alpha_max: int = 255
        self.chosen_target: int | None = None
        self.describer = describer

        if self.describer:
            self.describer.owner = self

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
        self.mission_board.fill_board(max_enemies_per_room=3, room_amount=3)
        flush_all()

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self) -> None:
        print(self.guild.get_dict())
        for entity in self.guild.roster:
            print(entity.get_dict())

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

        if "dying" in event:
            entity: Entity = event["dying"]

        if "retreat" in event:
            fighter: Fighter = event["retreat"]

            if fighter.owner.is_dead == False:
                self.guild.team.move_fighter_to_roster(fighter.owner)

        if "team triumphant" in event:
            guild: Guild = event["team triumphant"][0]
            dungeon: Dungeon = event["team triumphant"][1]
            dungeon.cleared = True
            guild.claim_rewards(dungeon)

    def _check_action_queue(self) -> None:
        for item in self.action_queue:
            print(f"item: {item}")

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
        if win:
            actions = self.team_triumphant_actions(self.guild, self.dungeon)
            self.guild.claim_rewards(self.dungeon)
        else:
            actions = self.team_defeated(self.guild.team)

        self.dungeon = None
        self.mission_in_progress = False
        return actions

    def init_dungeon(self) -> None:
        self.dungeon = self.mission_board.missions[self.selected_mission]

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
        quest = self.dungeon.room_generator()
        
        yield {
            "message": self.describer.describe_entrance()
        }

        for encounter in quest:

            healths = self.initial_health_values(
                self.guild.team.members, encounter.enemies
            )

            for h in healths:
                yield h

            while encounter.enemies and self.guild.team.members:
                # Beginning of encounter actions/state changes go here
                combat_round = CombatRound(
                    self.guild.team.members, encounter.enemies, self.await_input
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

            if len(self.guild.team.members) == 0:
                break

            if not self.dungeon.boss.is_dead:
                yield {"message": self.describer.describe_room_complete()}

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
