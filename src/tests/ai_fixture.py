import operator

from src.entities.action.actions import EndTurnAction, MoveAction
from src.entities.combat.fighter import Fighter


class TestAI:
    decision_log: list[dict]

    def __init__(
        self,
        preferred_choice: str,
        fallback_choices: tuple[str] = (MoveAction.name, EndTurnAction.name),
        max_decisions: int | None = None,
    ):
        self.preferred_choice = preferred_choice
        self.max_decisions = max_decisions
        self.total_decisions = 0
        self.decision_log = []
        self.fallback_choices = fallback_choices
        self._fallback_callback = lambda o: None
        self._current_fighter: Fighter | None = None

    def latest_decision(self) -> dict | None:
        latest = None
        if self.decision_log:
            latest = self.decision_log[-1]
        return latest

    def choose(self, event: dict):
        self.check_decision_count()

        choices = event.get("choices")
        self._current_fighter = event.get("await_input")
        if self._current_fighter is None:
            raise ValueError("No fighter to make decisions for!")
        if not choices:
            raise ValueError(f"Nothing to choose between, {event=}")

        if not (options := choices.get(self.preferred_choice)):
            options = self.try_fallbacks(choices)
            self._fallback_callback(options)
            self.count_decision()
            return

        if not options:
            raise ValueError(
                f"No actions of preferred type {self.preferred_choice} or fallbacks {self.fallback_choices} "
                f"were offered, got {choices.keys()=}"
            )

        choice = options[0]
        callback = choice.get("on_confirm")

        if not callable(callback):
            raise TypeError(f"The callback {choice.get('on_confirm')=} is not callable")
        self.decision_log.append(choice)
        callback()
        self.count_decision()

    def potential_targets(self):
        in_range = self._current_fighter.locatable.entities_in_range(
            self._current_fighter.encounter_context.get(),
            max_range=self._current_fighter.stats.max_range,
            entity_filter=lambda e: self._current_fighter.is_enemy_of(e.fighter),
        )
        return in_range

    def fallback_move_decision(self, options: list[dict]):
        nearest_enemy, _ = self._current_fighter.locatable.nearest_entity(
            self._current_fighter.encounter_context.get(),
            entity_filter=lambda e: self._current_fighter.is_enemy_of(e.fighter),
        )
        ideal_path = self._current_fighter.locatable.path_to_target(
            nearest_enemy.fighter
        )

        def _option_score(opt) -> int:
            score = 0
            for n1, n2 in zip(ideal_path, opt["subject"]):
                if n1 == n2:
                    score += 1
                else:
                    break
            return score

        ranked_options = sorted(options, key=_option_score, reverse=True)

        ranked_options[0]["on_confirm"]()

    def check_decision_count(self):
        if self.max_decisions is None:
            return

        if self.total_decisions >= self.max_decisions:
            raise RuntimeError(
                f"Hit specified max decisions. choice called "
                + f"{self.total_decisions + 1} times"
            )

    def count_decision(self):
        self.total_decisions += 1

    def try_fallbacks(self, choices: dict[str, list[dict]]) -> list[dict]:
        options = None
        for fallback in self.fallback_choices:
            if options := choices.get(fallback):
                if fallback == MoveAction.name:
                    self._fallback_callback = self.fallback_move_decision
                else:
                    self._fallback_callback = lambda opts: opts[0]["on_confirm"]()
                break

        return options
