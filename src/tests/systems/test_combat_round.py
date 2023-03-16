from unittest import TestCase

from src.entities.dungeon import Room
from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter
from src.systems.combat import CombatRound
from src.tests.fixtures import FighterFixtures


class CombatRoundTest(TestCase):
    @classmethod
    def get_entities(cls) -> tuple[Entity, Entity]:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )

        enemy = Entity(
            name=Name(first_name="baby", last_name="weak", title="the feeble"),
            fighter=Fighter(**FighterFixtures.baby(enemy=True, boss=False)),
        )

        return merc, enemy

    @classmethod
    def get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def set_up_encounter(cls, room_size: int, e1: Entity, e2: Entity) -> Room:
        room = cls.get_encounter(room_size)
        for entity in (e1, e2):
            room.add_entity(entity)

        e1.locatable.location = room.space.maxima.south.west
        e2.locatable.location = room.space.minima
        return room

    def test_combat_when_fighters_are_fast(self):
        # Arrange
        # =======
        merc, enemy = self.get_entities()
        merc.fighter.speed = 4

        # A fight in a phone booth
        self.set_up_encounter(10, merc, enemy)

        # Action
        # ======
        max_rounds, rounds = 20, 0
        combat_round = None
        while not merc.fighter.incapacitated and not enemy.fighter.incapacitated:
            combat_round = CombatRound([merc], [enemy])

            while combat_round.continues():
                for action in combat_round.do_turn():
                    # auto select first target
                    if sel := action.get("target_selection"):
                        assert sel["on_confirm"](
                            0
                        ), "Something went wrong while selecting a target"

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

        # A fight in a phone booth
        self.set_up_encounter(2, merc, enemy)

        # Action
        # ======
        combat_round = CombatRound([merc], [enemy])

        initiative_roll_actions, turn_actions = [], []

        initiative_roll_actions.extend(combat_round.initiative_roll_actions)

        # Assert
        # ======
        assert (
            len(initiative_roll_actions) == 1
            and "message" in initiative_roll_actions[0]
        ), (
            f"expected 2 entities in the turn order, \n"
            f"got {initiative_roll_actions=}\n"
        )

        round_gen = combat_round.do_turn()
        for action in round_gen:
            turn_actions.append(action)
            if sel := action.get("target_selection"):
                assert sel["on_confirm"](
                    0
                ), "we got an error while calling the on confirm"
                break

        dying_action = {}
        turns = [combat_round.do_turn(), combat_round.do_turn()]

        # iterate through the first turn
        for action in turns[0]:
            turn_actions.append(action)
            if sel := action.get("target_selection"):
                assert sel["on_confirm"](
                    0
                ), "Something went wrong while selecting a target"
            if "dying" in action:
                # if somebody got clapped, record that
                dying_action = action

        # if nobody got clapped, keep fighting
        if not dying_action:
            for action in turns[1]:
                turn_actions.append(action)

                if "dying" in action:
                    dying_action = action

        assert len(combat_round.teams[0]) == 1, (
            f"expected one merc remains, {combat_round.teams[0]=} and {combat_round.teams[1]=}\n"
            f"{merc.fighter=}, {merc.fighter.retreating=}\n"
            f"{enemy.fighter=}, {enemy.fighter.incapacitated=}\n"
        )
        assert dying_action, f"we expected a death, none occurred"
        assert (
            dying_action["dying"] is enemy
        ), f"the enemy should be dead, got {dying_action=}"
