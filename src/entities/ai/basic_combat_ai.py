from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from src.entities.action.actions import (
    ActionMeta,
    AttackAction,
    EndTurnAction,
    MoveAction,
)
from src.entities.ai.finite_state_machine import Callback, Machine, State

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter


class CombatAiState(State, metaclass=abc.ABCMeta):
    def choices_of(self, action: ActionMeta) -> list[dict]:
        co = self.working_set.get("choices", {}).get(action.name, [])
        return co

    def agent(self) -> Fighter:
        return self.working_set["await_input"]


class ChoosingTarget(CombatAiState):
    """
    This picks the closest enemy as a target for attack if possible. If no target can be reached
    it simply chooses to end its turn.
    """

    def next_state(self) -> State | None:
        fighter: Fighter = self.agent()

        if fighter is None:
            raise ValueError(f"{self.working_set=}")

        nearest = fighter.locatable.nearest_entity(
            room=fighter.encounter_context.get(),
            entity_filter=lambda e: e.fighter.is_enemy_of(fighter),
        )

        self.working_set["default"] = self.choices_of(EndTurnAction)[0].get(
            "on_confirm", lambda: None
        )

        if nearest is None:
            self.working_set["output"] = self.working_set["default"]
            return ActionChosen(self.working_set)
        else:
            self.working_set["target"] = nearest.fighter
            return ApproachingTarget(self.working_set)


class ApproachingTarget(CombatAiState):
    """
    This determines whether the fighter needs to move to the provided target,
    or if they are next to each other already, then choose who to attack.
    """

    def next_state(self) -> State | None:
        target: Fighter = self.working_set["target"]
        moves = self.choices_of(MoveAction)

        def ends_closest(option) -> int:
            _path = option["subject"]

            if target.locatable.path_to_destination(_path[-1]) is None:
                return 1000

            return len(target.locatable.path_to_destination(_path[-1]))

        ranked_moves = sorted(moves, key=ends_closest)
        best = ranked_moves[0]
        if AttackAction.all_available_to(self.agent()):
            if "target" in self.working_set:
                del self.working_set["target"]
            return ChoosingAttack(self.working_set)
        else:
            self.working_set["output"] = best["on_confirm"]
            return ActionChosen(self.working_set)


class ChoosingAttack(CombatAiState):
    """
    Determines of the available attack targets, which has the lowest health, and then attack that one.
    """

    def next_state(self) -> State | None:
        targets: list[dict] = self.choices_of(AttackAction)

        def lowest_health(target_choice: dict) -> int:
            return target_choice["subject"].health.current

        ranked_targets = sorted(targets, key=lowest_health)

        self.working_set["output"] = ranked_targets[0]["on_confirm"]
        return ActionChosen(self.working_set)


class ActionChosen(CombatAiState):
    def next_state(self) -> State | None:
        return None

    def output(self) -> Callback | None:
        return self.working_set.get("output", self.working_set["default"])


def decide(event) -> Callback | None:
    return Machine(ChoosingTarget, event).run()
