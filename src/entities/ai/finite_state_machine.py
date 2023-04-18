from __future__ import annotations

import abc
from typing import Callable

Callback = Callable[[], None]


class State(metaclass=abc.ABCMeta):
    name: str
    working_set: dict

    def __init__(self, working_set: dict):
        self.working_set = working_set

    @abc.abstractmethod
    def next_state(self) -> State | None:
        raise NotImplementedError()

    def output(self) -> Callback | None:
        return None


StateFactory = Callable[[dict], State]


class Machine:
    result: Callback | None

    def __init__(self, initial_state: StateFactory, working_set: dict | None = None):
        if working_set is None:
            working_set = {}

        self.working_set = working_set
        self.current_state = initial_state(self.working_set)
        self.result = None

    def tick(self):
        next_state = self.current_state.next_state()
        if next_state is None:
            self.result = self.current_state.output()
        else:
            self.current_state = next_state

    def run(self) -> Callback | None:
        while self.result is None:
            self.tick()

        return self.result
