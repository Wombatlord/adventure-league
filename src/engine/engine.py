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
Turn = Generator[None, None, Action]      # <-
Round = Generator[None, None, Turn]       # <- These are internal to the combat system
Encounter = Generator[None, None, Round]
Quest = Generator[None, None, Encounter]

projections = {
    "entity_data": [health]
}

def flush_all() -> None:
    for subscribers in projections.values():
        for subscriber in subscribers:
            subscriber.flush()


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
        self.combat_turn_order = []
        self.combat: Generator[None, None, Action] = None
        self.awaiting_input = False
        self.quest_complete = False
        self.message_alphas = []
        self.alpha_max = 255
    
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
        flush_all()

    def recruit_entity_to_guild(self, selection_id) -> None:
        self.guild.recruit(selection_id, self.entity_pool.pool)

    def print_guild(self):
        print(self.guild.get_dict())
        for entity in self.guild.roster:
            print(entity.get_dict())

    def process_action_queue(self):
        # new_action_queue = []
        # self._check_action_queue()
        while True:
            try:
                event = self.action_queue.pop(0)

            except IndexError:
                break
            
            self.process_one(event)

    def process_one(self, event: Action = None):
        print(f"{event=}, {type(event)=}")
        print(f"{projections=}, {type(projections)=}")
        
        if "message" in event:
            # print("message:", action["message"])
            self.messages.append(event["message"])

        to_project = {*event.keys()}&{*projections.keys()}
        for key in to_project:
            for projection in projections[key]:
                projection.consume(action=event)

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
            dungeon.cleared = True
            guild.claim_rewards(dungeon)

    def _check_action_queue(self):
        for item in self.action_queue:
            print(f"item: {item}")

    def last_n_messages(self, n: int) -> list[str]:
        return self.messages[-n:]

    def last_n_messages_with_alphas(self, n: int) -> MessagesWithAlphas:
        if len(self.message_alphas) < len(self.messages) and len(self.message_alphas) < n:
            self.message_alphas.insert(0, self.alpha_max)
            self.alpha_max -= 50
        
        return MessagesWithAlphas(self.messages[-n:], self.message_alphas)

    def await_input(self) -> None:
        self.awaiting_input = True

    def end_of_combat(self, win: bool = True) -> list[Action]:
        if win:
            actions = self.team_triumphant_actions(self.guild, self.dungeon)
            self.guild.claim_rewards(self.dungeon)
        else:
            actions = self.team_defeated(self.guild.team)
        
        self.dungeon = None
        return actions

    def init_combat(self):
        self.messages = []
        self.message_alphas = []
        self.alpha_max = 255
        self.dungeon = self.mission_board.missions[self.selected_mission]
        self.combat = self._generate_combat_actions()
    
    def initial_health_values(self, team, enemies) -> list:
        result = []
        for combatant in team:
            result.append(combatant.annotate_event({}))
        
        for combatant in enemies:
            result.append(combatant.annotate_event({}))

        return result
    
    def _generate_combat_actions(self) -> Generator[None, None, Action]:
        quest = self.dungeon.room_generator()

        for encounter in quest:
            
            healths = self.initial_health_values(self.guild.team.members, encounter.enemies)
            
            for health in healths:
            
                yield health

            while encounter.enemies and self.guild.team.members:
                # Beginning of encounter actions/state changes go here
                

                combat_round = CombatRound(self.guild.team.members, encounter.enemies, self.await_input)

                print("INITIATIVE ROLL")
                # example of per-round actions
                for action in combat_round.initiative_roll_actions:
                    yield action

                print("ROUND BEGINS")
                # then we begin iterating turns
                while combat_round.continues():
                    actions = combat_round.single_fighter_turn()
                    for action in actions:
                        yield action

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
