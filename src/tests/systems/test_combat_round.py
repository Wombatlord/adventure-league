from unittest import TestCase

from src.entities.action.actions import AttackAction, MoveAction
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name
from src.entities.item.inventory import Inventory
from src.systems.combat import CombatRound
from src.tests.ai_fixture import TestAI
from src.tests.fixtures import EncounterFactory, FighterFixtures
from src.world.level.room import Room
from src.world.node import Node


class CombatRoundTest(TestCase):
    fixtures = EncounterFactory

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
