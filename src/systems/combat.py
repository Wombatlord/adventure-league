from random import shuffle
from typing import Generator, Any, Callable
from enum import Enum

from src.entities.fighter import Fighter
from src.entities.entity import Entity

Action = dict[str, Any]
Hook = Callable[[], None]

class CombatHooks(Enum):
    INPUT_PROMPT = 0


class CombatRound:
    teams: tuple[list[Fighter], list[Fighter]]

    _result: bool | None
    _round_order: list[Fighter] = [] # fighter
    turn_complete: bool = False
    fighter_turns_taken: list[bool] = []

    def __init__(self, teamA: list[Entity], teamB: list[Entity], prompt_hook: Hook | None = None) -> None:
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
        
        for combatant in self._round_order:
            actions.append(combatant.owner.annotate_event({}))
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
        if len(self._round_order) == 0:
            # Stop the iteration when the round is over
            raise StopIteration(f"The turn order was empty, {self.teams[0]=}, {self.teams[1]=}")

        combatant = self._round_order.pop(0)
        if not combatant.is_enemy:
            hook = self.hooks.get(
                CombatHooks.INPUT_PROMPT, # The hook we want, if not supplied we default to:
                lambda :None              # a safe trivial callable
            )
            hook()
        
        _, opposing_team = self._team_id(combatant)

        enemies = []

        for team in self.teams:
            for fighter in team:
                if self._team_id(fighter)[0] == opposing_team and fighter.owner.is_dead is False:
                    enemies.append(fighter)
        
        if combatant.incapacitated == False:
            target_index = combatant.choose_target(enemies)
            target = enemies[target_index]
            
            # yield back the actions from the attack/damage taken immediately
            attack_result = combatant.attack(target.owner)
            print("CombatRound.single_fighter_turn: ", attack_result)
            yield attack_result 

            if (a := self._check_for_death(target)):
                yield a

            if (a := self._check_for_retreat(target)):
                yield a

    def _check_for_death(self, target) -> Action:
        name = target.owner.name.name_and_title
        if target.owner.is_dead:
            target.owner.die()
            return {"dying": target.owner, "message": f"{name} is dead!"}

        return {}


    def _check_for_retreat(self, fighter: Fighter) -> list[dict[str, str]]:
        if fighter.retreating == True:
            return {"retreat": fighter, "message": f"{fighter.owner.name.name_and_title} is retreating!"}

        return {}

    def victor(self) -> int | None:
        victor = None
        for team_idx in (0, 1):
            enemies = [
                cocombatant
                for cocombatant in self.teams[(team_idx + 1) % 2]
                if (cocombatant.incapacitated is False)
            ]

            # print(f"{team_idx=}; ", f"{enemies=}")

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


