from enum import Enum
from random import shuffle
from typing import Any, Callable, Generator

from src.entities.entity import Entity
from src.entities.fighter import Fighter

Action = dict[str, Any]
Hook = Callable[[], None]


class CombatHooks(Enum):
    INPUT_PROMPT = 0


class CombatRound:
    teams: tuple[list[Fighter], list[Fighter]]

    _result: bool | None
    _round_order: list[Fighter] = []  # fighter
    turn_complete: bool = False
    fighter_turns_taken: list[bool] = []

    def __init__(
        self, teamA: list[Entity], teamB: list[Entity], prompt_hook: Hook | None = None
    ) -> None:
        self.teams = (
            [member.fighter for member in teamA],
            [member.fighter for member in teamB],
        )
        self.initiative_roll_actions = self._roll_initiative()
        self.hooks = {}
        if prompt_hook:
            self.hooks = {CombatHooks.INPUT_PROMPT: prompt_hook}

    def _roll_initiative(self) -> list:
        actions = []

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
        actions.append(
            {
                "message": f"{self._round_order[0].owner.name.name_and_title} goes first this turn"
            }
        )

        return actions

    def _team_id(self, combatant) -> tuple[int, int]:
        team = 0
        if combatant in self.teams[1]:
            team = 1
        # return team, opposing_team
        return team, (team + 1) % 2

    def single_fighter_turn(self) -> Generator[None, None, Action]:
        """
        This will play out a turn if the current fighter at the start of the round order is an enemy.
        If the fighter is a player character, it will instead emit a request_target action from the fighter,
        initiating a transition into the player_fighter_turn() through the engines _generate_combat_actions() func.
        """
        if len(self._round_order) == 0:
            # Stop the iteration when the round is over
            raise StopIteration(
                f"The turn order was empty, {self.teams[0]=}, {self.teams[1]=}"
            )

        combatant = self._round_order.pop(0)

        _, opposing_team = self._team_id(combatant)

        enemies = []

        for team in self.teams:
            for fighter in team:
                if (
                    self._team_id(fighter)[0] == opposing_team
                    and fighter.owner.is_dead is False
                ):
                    enemies.append(fighter)

        if combatant.incapacitated == False:
            if combatant.is_enemy:
                # Play out the attack sequence for the fighter if it is an enemy and yield the actions.
                target_index = combatant.choose_nearest_target(enemies)

                target = enemies[target_index]

                # Move toward the target as far as speed allows
                move_result = combatant.locatable.approach_target(target)
                yield move_result

                # if we got to the destination and can attack, then attack
                if move_result.get("move", {})["in_motion"] is False:
                    # yield back the actions from the attack/damage taken immediately
                    yield combatant.attack(target.owner)

                if a := self._check_for_death(target):
                    yield a

                if a := self._check_for_retreat(combatant):
                    yield a

            if not combatant.is_enemy:
                # If the fighter is a player character, emit a target request action which will cause
                # the engine to await_input() and instead invoke player_fighter_turn() from eng._generate_combat_actions()
                yield combatant.request_target()

                # Insert the fighter back at the beginning of the turn order to be handled by player_fighter_turn()
                self._round_order.insert(0, combatant)

    def player_fighter_turn(self, target: int | None) -> Generator[None, None, Action]:
        """
        While eng.awaiting_input is True, this function will be repeatedly called in eng._generate_combat_actions()
        The target is passed in from that scope as eng.chosen_target, which is updated via the on_keypress hook of the MissionsView.
        While the target being passed is None, this function will continue to emit request_target actions which keeps the engine awaiting input.
        When a valid target is passed in, the turn will resolve the attack actions and yield them.
        eng.await_input is reset to False when the user presses space to advance after target selection, ending the calls to this function
        and continuing with eng._generate_combat_actions().
        """

        if len(self._round_order) == 0:
            # Stop the iteration when the round is over
            raise StopIteration(
                f"The turn order was empty, {self.teams[0]=}, {self.teams[1]=}"
            )

        combatant = self._round_order.pop(0)

        _, opposing_team = self._team_id(combatant)

        enemies = []

        for team in self.teams:
            for fighter in team:
                if (
                    self._team_id(fighter)[0] == opposing_team
                    and fighter.owner.is_dead is False
                ):
                    enemies.append(fighter)

        if combatant.incapacitated == False:
            if target is None or target > len(enemies) - 1:
                # If we don't have a valid target from the calling scope, keep the fighter at the start of the turn order
                # and emit another request for a target.
                self._round_order.insert(0, combatant)
                yield combatant.request_target()

            if target is not None and target <= len(enemies) - 1:
                # If the target is valid, then resolve the attack and yield the resulting actions for display when the user advances.
                target_index = target
                _target = enemies[target_index]

                # Move toward the target as far as speed allows
                move_result = combatant.locatable.approach_target(_target)
                yield move_result
                # if we got to the destination and can attack, then attack
                if move_result.get("move", {})["in_motion"] is False:
                    # yield back the actions from the attack/damage taken immediately
                    yield combatant.attack(_target.owner)

                if a := self._check_for_death(_target):
                    yield a

                if a := self._check_for_retreat(combatant):
                    yield a

    def _check_for_death(self, target) -> Action:
        name = target.owner.name.name_and_title
        if target.owner.is_dead:
            target.owner.die()
            return {"dying": target.owner, "message": f"{name} is dead!"}

        return {}

    def _check_for_retreat(self, fighter: Fighter) -> list[dict[str, str]]:
        result = {}
        if fighter.retreating == True:
            result.update(**fighter.owner.annotate_event({}))
            result.update(
                {
                    "retreat": fighter,
                    "message": f"{fighter.owner.name.name_and_title} is retreating!",
                }
            )
            return result

        return {}

    def victor(self) -> int | None:
        victor = None
        for team_idx in (0, 1):
            enemies = [
                cocombatant
                for cocombatant in self.teams[(team_idx + 1) % 2]
                if (cocombatant.incapacitated is False)
            ]

            if len(enemies) < 1:
                victor = team_idx
                break

        return victor

    def continues(self) -> bool:
        if self.victor() is None and self._round_order:
            return True

        return False

    def is_complete(self) -> bool:
        return not self.is_complete()
