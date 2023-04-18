import unittest

from src.entities.ai.finite_state_machine import Callback, Machine, State


class StateMachineTest(unittest.TestCase):
    def test_incrementing_state_machine_increments_number_up_to_configured_stop(self):
        # Arrange
        class Incrementing(State):
            def next_state(self) -> State:
                return Checking(
                    {
                        **self.working_set,
                        "count": self.working_set.get("count", 0) + 1,
                    }
                )

        class Done(State):
            def next_state(self) -> State | None:
                return None

            def output(self) -> Callback:
                return self.working_set["count"]

        class Checking(State):
            def next_state(self) -> State:
                if self.working_set.get("count", 0) < self.working_set.get("stop", 5):
                    return Incrementing(self.working_set)
                else:
                    return Done(self.working_set)

        m = Machine(Checking, {"count": 3, "stop": 100})

        # Action
        result = m.run()

        assert (
            result == 100
        ), f"Expected the state machine to give result 100, got {result=}"
