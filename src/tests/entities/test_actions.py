import unittest

from src.entities.action.actions import (
    ActionCompendium,
    ConsumeItemAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.action.weapon_action import WeaponAttackAction
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name
from src.entities.item.equipment import Equipment
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.entities.item.wieldables import Sword, Wieldable
from src.systems.combat import CombatRound
from src.tests.ai_fixture import TestAI
from src.tests.fixtures import EncounterFactory, FighterFixtures
from src.world.level.room import Room
from src.world.node import Node


class ActionsTest(unittest.TestCase):
    @classmethod
    def get_entities(cls) -> tuple[Entity, Entity]:
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )
        merc.fighter.equipment = Equipment(
            merc.fighter, weapon=Wieldable(owner=merc.fighter, item=Sword).on_equip()
        )
        merc.inventory = Inventory(owner=merc, capacity=1)
        enemy = Entity(
            name=Name(first_name="baby", last_name="weak", title="the feeble"),
            fighter=Fighter(**FighterFixtures.baby(enemy=True, boss=False)),
        )
        enemy.fighter.equipment = Equipment(
            merc.fighter, weapon=Wieldable(owner=merc.fighter, item=Sword).on_equip()
        )
        return merc, enemy

    @classmethod
    def get_potion(cls) -> HealingPotion:
        potion_entity = Entity()
        potion = HealingPotion(owner=potion_entity)
        return potion

    @classmethod
    def get_encounter(cls, size=2) -> Room:
        return Room((size, size))

    @classmethod
    def set_up_encounter(cls, room_size: int, e1: Entity, e2) -> Room:
        room = cls.get_encounter(room_size)
        room.add_entity(e1)
        room.add_entity(e2)

        e1.locatable.location = room.space.minima
        e2.locatable.location = room.space.maxima - Node(1, 1)
        return room

    def test_action_compendium_has_registered_all_actions(self):
        # Arrange
        keys = {"end turn", "weapon attack", "cast spell", "use item", "move"}
        actions = ActionCompendium.all_actions

        # Assert
        actual = {*actions.keys()}
        assert keys == actual, f"expected {keys=}, got {actual=}"

        # Check each key contains the correct ActionMeta
        assert actions.get("end turn") is EndTurnAction
        assert actions.get("weapon attack") is WeaponAttackAction
        assert actions.get("use item") is ConsumeItemAction
        assert actions.get("move") is MoveAction

    def test_request_action_event_schema(self):
        # Arrange
        merc, enemy = self.get_entities()
        potion = self.get_potion()
        merc.inventory.add_item_to_inventory(potion)
        room = self.set_up_encounter(10, merc, enemy)
        merc.fighter.encounter_context.set(room)

        # Action
        event = next(merc.fighter.request_action_choice())

        # Assert
        assert isinstance(event, dict)
        assert isinstance(event["choices"], dict)
        choices = event.get("choices")

        for option_list in choices.values():
            for option in option_list:
                self._assert_schema(option)

    def _assert_schema(self, option: dict):
        assert type(option.get("name")) is str
        assert type(option.get("actor")) is Fighter
        assert type(option.get("cost")) is int
        assert callable(option.get("on_confirm"))

        destination = option.get("destination")
        assert destination is None or isinstance(
            destination, Node
        ), f"expected Node or None, got {type(destination)=}"

        path = option.get("path")
        assert path is None or isinstance(path, tuple)
        if path:
            assert all(isinstance(item, Node) for item in path)


def _assert_keys(msg: dict | None = None, expected_keys: set[str] | None = None):
    msg = msg or {}
    expected_keys = expected_keys or set()

    actual_keys = {*msg.keys()}
    assert (
        actual_keys == expected_keys
    ), f"Incorrect msg schema: {expected_keys=}, got {msg=}."


class EndTurnActionTest(unittest.TestCase):
    fixtures = EncounterFactory

    def test_end_turn_ends_fighter_turn_when_no_other_actions_taken(self):
        # Arrange
        room, mercs, enemies = self.fixtures.one_vs_one_enemies_lose(room_size=10)
        combat_round = CombatRound(mercs, enemies)
        current_fighter: Fighter | None = None
        ai = TestAI(preferred_choice=EndTurnAction.name)
        # Action
        turn = combat_round.do_turn()
        for event in turn:
            if current_fighter := event.get("await_input"):
                ai.choose(event)
                break

        # Assert
        assert current_fighter is not None
        assert current_fighter.is_ready_to_act()

        _assert_keys(msg=next(turn), expected_keys={"message"})
        _assert_keys(msg=next(turn), expected_keys={"turn_end"})


class MoveActionTest(unittest.TestCase):
    fixtures = EncounterFactory

    def test_move_action_deducts_correct_cost_and_emits_events(self):
        # === Arrange ===
        room, mercs, enemies = self.fixtures.one_vs_one_enemies_lose(room_size=10)
        combat_round = CombatRound(mercs, enemies)
        ai = TestAI(preferred_choice=MoveAction.name)
        current_fighter: Fighter | None = None

        # === Action ===
        turn = combat_round.do_turn()
        for event in turn:
            # pull the current fighter from the await_input event
            if current_fighter := event.get("await_input"):
                ai.choose(event)
                break

        # === Assert ===
        assert current_fighter is not None
        assert current_fighter.is_ready_to_act()
        assert (
            current_fighter.action_points.current
            == current_fighter.action_points.per_turn
        )

        # Checking the ai had all the info it needed
        decision = ai.latest_decision()
        _assert_keys(
            msg=decision,
            expected_keys={"name", "actor", "cost", "subject", "on_confirm", "label"},
        )

        # this has to be calculated now, if we get it later the fighter has reached their destination and
        # incurred the cost
        cost = MoveAction.cost(
            fighter=current_fighter, destination=decision["subject"][-1]
        )
        expected_points_remaining = current_fighter.action_points.per_turn - cost

        # assert the turn generator gives us a series of moves
        chosen_path = decision["subject"]
        step_event: dict | None = None
        for _ in range(len(chosen_path[1:])):
            step_event = next(turn)
            _assert_keys(msg=step_event, expected_keys={"move"})

        # assertions about the final step
        assert not step_event["move"][
            "in_motion"
        ], f"expected false from {step_event['move']['in_motion']=}"

        # use the predicted points remaining to verify the cost is deducted correctly
        actual_points_remaining = current_fighter.action_points.current
        assert (
            actual_points_remaining == expected_points_remaining
        ), f"Cost incorrectly applied {expected_points_remaining=}, got {actual_points_remaining=}"

        # assert that the move did not use all of the points
        assert actual_points_remaining > 0

        # Check that the next event is a request for more instructions
        event = next(turn)
        assert (
            "await_input" in event
        ), f"The next event should be another request for input, got {event}"
