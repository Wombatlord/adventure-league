from unittest import TestCase

from src.entities.actions import AttackAction, MoveAction
from src.entities.dungeon import Room
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.entities.inventory import Inventory
from src.systems.combat import CombatRound
from src.tests.ai_fixture import TestAI
from src.tests.fixtures import FighterFixtures
from src.world.node import Node


class CombatRoundTest(TestCase):
    @classmethod
    def get_aggressive_ai(self, max_decisions: int) -> TestAI:
        return TestAI(
            AttackAction.name,
            fallback_choices=(MoveAction.name,),
            max_decisions=max_decisions,
        )

    @classmethod
    def get_entities(cls) -> tuple[Entity, Entity]:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )
        merc.inventory = Inventory(owner=merc, capacity=1)
        enemy = Entity(
            name=Name(first_name="baby", last_name="weak", title="the feeble"),
            fighter=Fighter(**FighterFixtures.baby(enemy=True, boss=False)),
        )
        enemy.inventory = Inventory(owner=enemy, capacity=1)
        return merc, enemy

    @classmethod
    def get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def set_up_encounter(cls, room_size: int, e1: Entity, e2: Entity) -> Room:
        room = cls.get_encounter(room_size)
        for entity in (e1, e2):
            room.add_entity(entity)

        e1.locatable.location = room.space.maxima - Node(1, 1)
        e2.locatable.location = room.space.minima

        return room

    def test_combat_when_fighters_are_fast(self):
        # Arrange
        # =======
        merc, enemy = self.get_entities()
        ai = self.get_aggressive_ai(max_decisions=100)
        merc.fighter.speed = 4

        # A fight in a phone booth
        self.set_up_encounter(10, merc, enemy)
        max_rounds, rounds = 20, 0
        combat_round = None

        # Action
        # ======
        while not merc.fighter.incapacitated and not enemy.fighter.incapacitated:
            combat_round = CombatRound([merc], [enemy])
            while combat_round.continues():
                for event in combat_round.do_turn():
                    # auto select first target
                    if "await_input" in event:
                        fighter = event["await_input"]
                        ai.choose(event)
                        assert fighter.is_ready_to_act()

            # assert we're actually progressing the state
            assert (
                rounds < max_rounds
            ), f"hit max rounds. Locations: {merc.locatable.location=}, {enemy.locatable.location=}"
            rounds += 1

        assert not combat_round.continues(), "Combat should not be continuing now"
        assert (
            combat_round and combat_round.victor() is not None
        ), "No clear winner, seems sus."

    def test_asymmetrical_combat_ends_after_first_round(self):
        # Arrange
        # =======
        merc, enemy = self.get_entities()
        ai = self.get_aggressive_ai(max_decisions=10)

        # A fight in a phone booth
        self.set_up_encounter(2, merc, enemy)

        # Action
        # ======
        combat_round = CombatRound([merc], [enemy])

        initiative_roll_events, turn_events = [], []

        initiative_roll_events.extend(combat_round.initiative_roll_events)

        # Assert
        # ======
        assert (
            len(initiative_roll_events) == 1 and "message" in initiative_roll_events[0]
        ), (
            f"expected 2 entities in the turn order, \n"
            f"got {initiative_roll_events=}\n"
        )

        round_gen = combat_round.do_turn()
        for event in round_gen:
            turn_events.append(event)
            if "await_input" in event:
                ai.choose(event)
                break

        dying_event = {}
        turns = [combat_round.do_turn(), combat_round.do_turn()]

        # iterate through the first turn
        for event in turns[0]:
            turn_events.append(event)
            if "await_input" in event:
                ai.choose(event)
            if "dying" in event:
                # if somebody got clapped, record that
                dying_event = event

        # if nobody got clapped, keep fighting
        if not dying_event:
            for event in turns[1]:
                turn_events.append(event)

                if "dying" in event:
                    dying_event = event

        assert len(combat_round.teams[0]) == 1, (
            f"expected one merc remains, {combat_round.teams[0]=} and {combat_round.teams[1]=}\n"
            f"{merc.fighter=}, {merc.fighter.retreating=}\n"
            f"{enemy.fighter=}, {enemy.fighter.incapacitated=}\n"
        )
        assert dying_event, f"we expected a death, none occurred"
        assert (
            dying_event["dying"] is enemy
        ), f"the enemy should be dead, got {dying_event=}"
