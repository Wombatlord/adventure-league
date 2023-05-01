from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.ai import basic_combat_ai

if TYPE_CHECKING:
    from src.engine.engine import Engine

from abc import ABCMeta, abstractmethod


class CombatAISubscriber:
    def __init__(self, eng: Engine) -> None:
        eng.static_subscribe(
            topic="await_input",
            handler_id=f"{self.__class__.__name__}.handle",
            handler=self.handle,
        )

    def handle(self, event: dict) -> None:
        if awaiting := event.get("await_input"):
            if ai := awaiting.owner.ai:
                ai.choose(event)


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


def _copy(d: dict | list) -> dict | list:
    # dict case, iterate over items, copying the value and inserting it into frest
    # dict at the corresponding key.
    if isinstance(d, dict):
        result = {}
        for k, v in d.items():
            result[k] = _copy(v)
        return result

    # list case iterates over items, appending them to a freshly instantiated list
    elif isinstance(d, list):
        result = []
        for item in d:
            result.append(_copy(item))
        return result

    # any other type is returned as-is
    else:
        return d


class BasicCombatAi(AiInterface):
    def choose(self, event: dict):
        callback = basic_combat_ai.decide(_copy(event))
        callback()
