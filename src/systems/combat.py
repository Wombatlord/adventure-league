from enum import Enum
from random import shuffle
from typing import Any, Callable, Generator, NamedTuple

from src.entities.actions import EndTurnAction
from src.entities.entity import Entity
from src.entities.fighter import Fighter
from src.entities.items import HealingPotion

Event = dict[str, Any]
Hook = Callable[[], None]


class CombatHooks(Enum):
    INPUT_PROMPT = 0


class Teams(NamedTuple):
    current: int
    opposing: int


class CombatRound:
    teams: tuple[list[Fighter], list[Fighter]]

    _result: bool | None
    _round_order: list[Fighter] = []  # fighter
    turn_complete: bool = False
    fighter_turns_taken: list[bool] = []

    def __init__(self, team_a: list[Entity], team_b: list[Entity]) -> None:
        self.teams = (
            [member.fighter for member in team_a],
            [member.fighter for member in team_b],
        )
        self.initiative_roll_events = self._roll_initiative()

    def _roll_initiative(self) -> list[Event]:
        events = []

        combatants = [
            yob for yob in self.teams[0] + self.teams[1] if yob.incapacitated == False
        ]

        battle_size = len(combatants)

        # roll initiatives and sort desc
        initiatives = [*range(0, battle_size)]

        # assing shuffled initatives to combatants
        shuffle(initiatives)
        initiative_roll = zip(combatants, initiatives)
        initiative_roll = sorted(
            initiative_roll, key=lambda item: item[1], reverse=True
        )

        # drop the initiative for the turn order since the index is the battle_size - (initiative + 1)
        self._round_order = [combatant for combatant, _ in initiative_roll]
        events.append(
            {
                "message": f"{self._round_order[0].owner.name.name_and_title} goes first this turn"
            }
        )

        return events

    def teams_of(self, combatant) -> Teams:
        team = 0
        if combatant in self.teams[1]:
            team = 1
        # return team, opposing_team
        return Teams(current=team, opposing=(team + 1) % 2)

    def in_play(self, fighter: Fighter, opposing_team: int) -> bool:
        return (
            self.teams_of(fighter).current == opposing_team
            and not fighter.owner.is_dead
            and not fighter.retreating
        )

    def get_enemies(self, opposing_team) -> list[Fighter]:
        return list(
            filter(
                lambda f: self.in_play(f, opposing_team),
                self.teams[0] + self.teams[1],
            )
        )

    def do_turn(self) -> Generator[Event, None, None]:
        """
        This will play out a turn if the current fighter at the start of the round order is an enemy.
        If the fighter is a player character, it will instead emit a request_target event from the fighter,
        initiating a transition into the player_turn() through the engines _generate_combat_events() func.
        """
        if len(self._round_order) == 0:
            # Stop the iteration when the round is over
            raise StopIteration(
                f"The turn order was empty, {self.teams[0]=}, {self.teams[1]=}"
            )

        combatant = self.current_combatant()
        combatant.on_turn_start()
        opposing_team = self.teams_of(combatant).opposing
        enemies = self.get_enemies(opposing_team)

        if combatant.incapacitated:
            raise Exception(f"Incapacitated combatant {combatant.get_dict()}: oops!")

        # INTEGRATING WITH ACTIONS
        # TODO: before we can test this
        #  - In self.advance there are some state integrity checks around death and dishonour
        while combatant.can_act():
            # ready an action
            yield from combatant.request_action_choice()

            if not combatant.is_ready_to_act():
                # if still not ready, from the top
                continue
            else:
                # otherwise do that action!
                yield from combatant.act()
                yield from self._check_for_death(enemies)
                yield from self._check_for_retreat(
                    self.teams[self.teams_of(combatant).current]
                )

    def gather_turn_choices(
        self, combatant: Fighter, enemies: list[Fighter]
    ) -> Generator[Event, None, None]:
        # If no item is explicitly chosen, a trivial consumable with no effects/message is chosen
        if combatant.is_enemy:
            yield combatant.choose_item()
        else:
            yield combatant.request_item_use()

        # If the combatant cannot acquire a target for whatever reason, this
        # will hold up combat forever!
        has_notified_item = False
        while not combatant.current_target() and not combatant.turn_is_forfeit():
            if combatant.is_enemy:
                yield combatant.choose_nearest_target(enemies)
            else:
                if (
                    item_name := combatant.chosen_consumable().name
                ) and not has_notified_item:
                    has_notified_item = True
                    yield {"message": f"{combatant.owner.name} will use a {item_name}"}

                yield from combatant.request_target(enemies)

    def execute_turn_choices(self, combatant: Fighter) -> Generator[Event, None, None]:
        # Move toward the target as far as speed allows
        yield from combatant.consume_item()
        target = combatant.current_target()
        step = {}
        for step in combatant.locatable.approach_target(target):
            yield step

        target_reached = step.get("move", {})["in_motion"] is False
        if target_reached:
            yield combatant.attack()

        combatant._prev_target = target
        combatant.provide_target(None)

        yield from self._check_for_death(target)

        yield from self._check_for_retreat(combatant)

    def _check_for_death(self, team) -> Event:
        for target in team:
            name = target.owner.name.name_and_title
            if target.owner.is_dead:
                target.owner.die()
                self._purge_fighter(target)

                yield {"dying": target.owner, "message": f"{name} is dead!"}

    def _check_for_retreat(self, team) -> Event:
        for fighter in team:
            if fighter.retreating:
                result = {}
                self._purge_fighter(fighter)

                result.update(**fighter.owner.annotate_event({}))
                result.update(
                    {
                        "retreat": fighter,
                        "message": f"{fighter.owner.name.name_and_title} is retreating!",
                    }
                )

                yield result

    def _purge_fighter(self, fighter: Fighter) -> None:
        team_id = 0 if fighter in self.teams[0] else 1
        self.teams[team_id].remove(fighter)

        if fighter in self._round_order:
            self._round_order.remove(fighter)

    def victor(self) -> int | None:
        match tuple(len(t) for t in self.teams):
            case (x, 0) if x != 0:
                return 0
            case (0, x) if x != 0:
                return 1
            case _:
                return None

    def continues(self) -> bool:
        if self.victor() is None and self._round_order:
            return True

        return False

    def is_complete(self) -> bool:
        return not self.is_complete()

    def current_combatant(self, pop=False) -> Fighter | None:
        if self._round_order:
            if pop:
                return self._round_order.pop(0)
            return self._round_order[0]

        return None
