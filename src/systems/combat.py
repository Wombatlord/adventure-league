from enum import Enum
from random import shuffle
from typing import Any, Callable, Generator, NamedTuple

from src.entities.entity import Entity
from src.entities.fighter import Fighter

Action = dict[str, Any]
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
        for i, entity in enumerate(teamA):
            entity.fighter.on_retreat_hooks.append(
                lambda e: len(self.teams[0]) > i and self.teams[0].pop(i)
            )
        for i, entity in enumerate(teamB):
            entity.fighter.on_retreat_hooks.append(
                lambda e: len(self.teams[0]) > i and self.teams[1].pop(i)
            )

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

    def ai_turn(self) -> Generator[None, None, Action]:
        """
        This will play out a turn if the current fighter at the start of the round order is an enemy.
        If the fighter is a player character, it will instead emit a request_target action from the fighter,
        initiating a transition into the player_turn() through the engines _generate_combat_actions() func.
        """
        if len(self._round_order) == 0:
            # Stop the iteration when the round is over
            raise StopIteration(
                f"The turn order was empty, {self.teams[0]=}, {self.teams[1]=}"
            )

        combatant = self.current_combatant()
        opposing_team = self.teams_of(combatant).opposing
        enemies = self.get_enemies(opposing_team)

        if combatant.incapacitated:
            raise Exception(f"Incapacitated combatant {combatant.get_dict()}: oops!")

        if not combatant.is_enemy:
            # If the fighter is a player character, emit a target request action which will cause
            # the engine to await_input() and instead invoke player_turn() from
            # eng._generate_combat_actions()
            yield combatant.request_target(enemies)
        else:
            # Play out the attack sequence for the fighter if it is an enemy and yield the actions.
            target_index = combatant.choose_nearest_target(enemies)
            target = enemies[target_index]
            combatant = self.current_combatant(pop=True)
            yield from self.advance(combatant, target)

    def player_turn(self, target: int | None) -> Generator[Action, None, None]:
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

        combatant = self.current_combatant()
        opposing_team = self.teams_of(combatant).opposing
        enemies = self.get_enemies(opposing_team)

        if combatant.incapacitated:
            raise Exception(f"Incapacitated combatant {combatant.get_dict()}: oops!")

        if target is None:
            yield combatant.request_target(enemies)
        elif target not in range(len(enemies)):
            # If we don't have a valid target from the calling scope, keep the fighter at the start of the turn
            # order and emit another request for a target.
            yield combatant.request_target(enemies)
        else:
            # If the target is valid, then resolve the attack and yield the resulting actions for display when the
            # user advances.
            target_index = target
            target = enemies[target_index]
            combatant = self.current_combatant(pop=True)
            yield from self.advance(combatant, target)

    def advance(self, combatant, target):
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

    def _check_for_death(self, target) -> Action:
        name = target.owner.name.name_and_title
        if target.owner.is_dead:
            target.owner.die()
            if target in self._round_order:
                self._round_order = [c for c in self._round_order if c is not target]
            return {"dying": target.owner, "message": f"{name} is dead!"}

        return {}

    def _check_for_retreat(self, fighter: Fighter) -> list[dict[str, str]]:
        result = {}
        if fighter.retreating == True:
            if fighter in self._round_order:
                self._round_order = [c for c in self._round_order if c is not fighter]

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

    def current_combatant(self, pop=False) -> Fighter | None:
        if self._round_order:
            if pop:
                return self._round_order.pop(0)
            return self._round_order[0]

        return None
