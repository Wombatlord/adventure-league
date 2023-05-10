from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.engine import Engine

from abc import ABCMeta, abstractmethod

from src.entities.ai import basic_combat_ai
from src.utils.deep_copy import copy


class CombatAISubscriber:
    @classmethod
    def handle(cls, event: dict) -> None:
        if awaiting := event.get("await_input"):
            if ai := awaiting.owner.ai:
                ai.choose(event)


def subscribe(eng: Engine):
    eng.static_subscribe(
        topic="await_input",
        handler_id=f"{CombatAISubscriber.__name__}.handle",
        handler=CombatAISubscriber.handle,
    )


class AiInterface(metaclass=ABCMeta):
    @abstractmethod
    def choose(self, event: dict):
        ...


class NoCombatAI(AiInterface):
    preferred_choice = "end turn"

    def __init__(self, owner):
        self.owner = owner

    def choose(self, event: dict):
        choices = event.get("choices")
        if not choices:
            return

        options = choices.get(self.preferred_choice)
        if not options:
            return

        choice = options[0]
        callback = choice.get("on_confirm")
        if not callable(callback):
            return

        callback()


class BasicCombatAi(AiInterface):
    def choose(self, event: dict):
        callback = basic_combat_ai.decide(copy(event))
        callback()
