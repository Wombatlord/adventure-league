from __future__ import annotations

import math
import random
import time
from typing import Callable, Hashable, NamedTuple, Self

from src.config import DEBUG

# breakpoint = lambda: None


class Observation(Hashable):
    def compatibilities(self, side: Side) -> set[Self]:
        NotImplementedError()


CollapseResult = dict[tuple[int, int], Observation]


class config:
    WIDTH = 10
    HEIGHT = 10
    ENTROPY_RESOLUTION = 1 / 1000

    @classmethod
    def set_dims(cls, width: int | None = None, height: int | None = None):
        cls.WIDTH = width or cls.WIDTH
        cls.HEIGHT = height or cls.HEIGHT

    @classmethod
    def reset_dims(cls):
        cls.set_dims(10, 10)


class Side(int):
    def side_string(self) -> str:
        return ["N", "E", "S", "W"][self]

    def opposite(self) -> Self:
        return [
            SOUTH,
            WEST,
            NORTH,
            EAST,
        ][self]


NORTH = Side(0)
EAST = Side(1)
SOUTH = Side(2)
WEST = Side(3)

SIDE_COUNT = 4


class Pos(NamedTuple):
    x: int = 0
    y: int = 0

    @classmethod
    def from_index(cls, idx: int) -> Pos:
        return cls(idx % config.WIDTH, idx // config.WIDTH)

    def __str__(self) -> str:
        return f"{self.x}, {self.y}"

    def __eq__(self, __value: object) -> bool:
        return self.x == __value.x and self.y == __value.y

    def in_bounds(self) -> bool:
        return (
            self.x >= 0
            and self.y >= 0
            and self.x < config.WIDTH
            and self.y < config.HEIGHT
        )

    def next(self) -> Self | None:
        x = (self.x + 1) % config.WIDTH
        y = self.y

        if x == 0:
            y += 1

        if y == config.HEIGHT:
            return None

        return Pos(x, y)

    def adjacent(self, side: Side) -> Self | None:
        a: Pos | None = None

        match side.side_string():
            case "N":
                a = Pos(self.x, self.y - 1)
            case "E":
                a = Pos(self.x + 1, self.y)
            case "S":
                a = Pos(self.x, self.y + 1)
            case "W":
                a = Pos(self.x - 1, self.y)

        if not a.in_bounds():
            return None

        return a

    def cardinal(self) -> tuple[Pos | None, Pos | None, Pos | None, Pos | None]:
        positions = [Pos(), Pos(), Pos(), Pos()]
        dirs = [NORTH, EAST, SOUTH, WEST]
        for i in range(4):
            positions[i] = self.adjacent(dirs[i])

        return positions

    def idx(self) -> int:
        return self.y * config.WIDTH + self.x


class VisitQueue:
    states: list[Pos]

    def __init__(self):
        self.positions = []

    def join_from(self, visited: list[bool]):
        positions = [
            Pos.from_index(idx)
            for idx, was_visited in enumerate(visited)
            if was_visited
        ]
        self.positions = positions + self.positions

    def latest_n(self, n: int) -> list[Pos]:
        if len(self.positions) >= n:
            return self.positions[:n]
        return self.positions


class WaveFunction:
    states: list[StateVec]
    visit_history: VisitQueue

    def __init__(self, states: states) -> None:
        self.states = states
        self.visit_history = VisitQueue()

    def __str__(self) -> str:
        g_string = ""

        for row in self.rows():
            g_string += "".join([f"{t}" for t in row])
            g_string += "\n"

        return g_string

    def choose_state(self) -> CollapseResult:
        return {tuple(s.pos): s.enumerate_outcomes().pop() for s in self.states}

    def state_at(self, pos: Pos) -> StateVec:
        if pos is None:
            return

        return self.states[pos.idx()]

    def rows(self) -> list[list[StateVec]]:
        rows = []

        states = [*self.states]

        while states:
            row, states = states[: config.WIDTH], states[config.WIDTH :]
            rows.append(row)

        return rows

    @classmethod
    def from_factory(cls, factory: Callable[[Pos], StateVec]):
        states = []
        for idx in range(config.WIDTH * config.HEIGHT):
            pos = Pos.from_index(idx)
            states.append(factory(pos))

        return cls(states)

    def get_next(self) -> StateVec:
        lowest_entropy = None
        for idx, state_vec in enumerate(self.states):
            if state_vec is None:
                raise TypeError(
                    f"Values in the wavefunction should never be None. Details: {idx=}, {Pos.from_index(idx)=}"
                )

            if state_vec.is_collapsed():
                continue

            if lowest_entropy is None:
                lowest_entropy = state_vec.entropy()

            elif state_vec.entropy() < lowest_entropy:
                lowest_entropy = state_vec.entropy()

        if lowest_entropy is None:
            return None

        states_with_entropy = [
            *filter(
                lambda s: abs(s.entropy() - lowest_entropy) < config.ENTROPY_RESOLUTION,
                self.states,
            )
        ]
        nxt = random.choice(states_with_entropy)

        return nxt


def flat_distribution(allowed_states) -> Callable[[Pos], StateVec]:
    def factory(pos: Pos) -> StateVec:
        sv = StateVec(pos, allowed_states)

        for s in allowed_states:
            sv.set_state_frequency(s, 1)

        return sv

    return factory


def from_distribution(dist: dict[Observation, int]) -> Callable[[Pos], StateVec]:
    def factory(pos: Pos) -> StateVec:
        sv = StateVec(pos, dist.keys())

        for s, freq in dist.items():
            sv.set_state_frequency(s, freq)

        return sv

    return factory


visited = []


class StateResolutionError(ValueError):
    state_vec: StateVec
    visited: list[bool]
    wave_function: WaveFunction | None

    @classmethod
    def contradictory_state(
        cls,
        state_vec: StateVec,
        visited: list[bool],
        wave_function: WaveFunction | None = None,
    ) -> Self:
        msg = f"Reached a contradictory state while resolving state at {state_vec.pos}"
        instance = cls(msg)
        instance.state_vec = state_vec
        instance.visited = visited
        instance.wave_function = wave_function
        return instance


class IrreconcilableStateError(ValueError):
    wave_function: WaveFunction

    @classmethod
    def create(cls, wf: WaveFunction) -> Self:
        msg = f"Reached the maximum number of retries while attempting to totally collapse the wavefunction."
        instance = cls(msg)
        instance.wave_function = wf
        return instance


class StateVec:
    allowed_states: list[Observation]
    state_counts: dict[Observation, int]
    pos: Pos

    def __init__(
        self,
        pos: Pos,
        allowed_states: list[Observation],
        state_counts: dict[Observation, int] | None = None,
    ):
        self.allowed_states = allowed_states
        self.state_counts = state_counts or {}
        self.pos = pos

    def set_state_frequency(self, state: Observation, count: int):
        self.state_counts[state] = count

    def count_state_occurrence(self, state: Observation):
        self.state_counts[state] = self.state_counts.get(state, 0) + 1

    def is_collapsed(self) -> bool:
        return len(self.enumerate_outcomes()) == 1

    def total(self) -> int:
        d = 0
        for v in self.state_counts.values():
            d += v

        return d

    def __str__(self) -> str:
        if self.is_collapsed():
            return str([*self.enumerate_outcomes()][0])
        else:
            return "·"

    def observe(self, wf: WaveFunction):
        # global visited
        state_list = []
        for state, frequency in self.state_counts.items():
            state_list += [state] * frequency

        state = random.choice(state_list)
        self.state_counts = {s: int(s == state) for s in self.allowed_states}

        visited = [False for _ in range(config.WIDTH * config.HEIGHT)]

        self._propagate(wf, visited)
        wf.visit_history.join_from(visited)

    def _propagate(self, wf: WaveFunction, visited: list[bool]):
        is_visited = lambda ts: visited[ts.pos.idx()]

        if is_visited(self):
            return
        visited[self.pos.idx()] = True

        lowest_entropy_neighbour: StateVec | None = None
        states_culled = 0

        for pos in self.pos.cardinal():
            if pos is None:
                continue

            neighbour = wf.state_at(pos)
            if neighbour is None:
                continue

            if is_visited(neighbour):
                continue

            states_culled += neighbour.constrain(wf)

            if lowest_entropy_neighbour is None:
                lowest_entropy_neighbour = neighbour

            elif lowest_entropy_neighbour.entropy() >= neighbour.entropy():
                lowest_entropy_neighbour = neighbour

        if lowest_entropy_neighbour is None or states_culled == 0:
            return

        lowest_entropy_neighbour._propagate(wf, visited)

    def constrain(self, wf: WaveFunction) -> int:
        initial = self.total()

        for _s, pos in enumerate(self.pos.cardinal()):
            if pos is None:
                continue

            neighbour = wf.state_at(pos)
            side = Side(_s)

            if neighbour is None:
                continue

            neighbour_states = neighbour.enumerate_outcomes()

            compatible_with = self.states_compatible_with(side, neighbour_states)

            self.state_counts = compatible_with

            if self.total() == 0:
                raise StateResolutionError.contradictory_state(self, visited, wf)

        culled = initial - self.total()
        return culled

    def enumerate_outcomes(self) -> set[Observation]:
        return {outcome for outcome, count in self.state_counts.items() if count}

    def entropy(self) -> float:
        t = self.total()
        probability = lambda s: self.state_counts[s] / t
        try:
            entropy = 0
            for state in self.allowed_states:
                p = probability(state)
                if not p:
                    continue

                entropy += -math.log(p) * p

            return entropy
        except ZeroDivisionError as e:
            raise StateResolutionError.contradictory_state(self, [], None) from e

    def has_same_entropy(self, other: Self) -> bool:
        my_freq_freq = {}
        other_freq_freq = {}
        for s in self.allowed_states:
            my_freq_freq[self.state_counts[s]] = (
                my_freq_freq.get(self.state_counts[s], 0) + 1
            )
            other_freq_freq[other.state_counts[s]] = (
                other_freq_freq.get(other.state_counts[s], 0) + 1
            )

        return my_freq_freq == other_freq_freq

    def states_compatible_with(
        self, side: Side, outcomes: set[Observation]
    ) -> dict[Observation, int]:
        # initialise a full counts vector with zero for every state
        compatible_freqs = {s: 0 for s in self.allowed_states}

        # work out the complete set of states that are consistent with the neighbours possible outcomes
        compatible_states = set()
        for outcome in outcomes:
            compatible_states = compatible_states | outcome.compatibilities(
                side.opposite()
            )

        # work out the state counts with that restriction applied
        for state, frequency in self.state_counts.items():
            if state in compatible_states:
                compatible_freqs[state] = frequency

        return compatible_freqs


def iter_one_from(wf: WaveFunction, p: Pos) -> StateVec | None:
    if not p.in_bounds():
        return None

    state_vec = wf.state_at(p)

    if state_vec is None:
        return None

    if state_vec.total() == 0:
        raise StateResolutionError.contradictory_state(state_vec, [], wf)

    state_vec.observe(wf)

    return wf.get_next()


def generate(
    factory: Callable[[Pos], StateVec], max_retries: int = 3
) -> CollapseResult:
    return iterate_with_backtracking(
        iterator=iter_one_from, factory=factory, max_retries=max_retries
    )


def iterate_with_backtracking(
    iterator: Callable[[WaveFunction, Pos], StateVec | None],
    factory: Callable[[Pos], StateVec],
    max_retries=3,
) -> CollapseResult:
    wave_function = WaveFunction.from_factory(factory)
    current_pos = wave_function.get_next().pos

    def _robust_iterator(
        wf: WaveFunction, pos: Pos
    ) -> tuple[StateVec | None, StateResolutionError | None]:
        try:
            return iterator(wf, pos), None
        except StateResolutionError as e:
            return wf.state_at(pos), e

    def decohere_invalid_state(wf: WaveFunction, failed_pos: Pos, recurse: int = 0):
        neighbour_positions = [p for p in failed_pos.cardinal() if p is not None] + [
            failed_pos
        ]
        # reset states completely
        for pos in neighbour_positions:
            wf.states[pos.idx()] = factory(pos)

        if recurse:
            # do that for the nearest neighbours
            for pos in [*neighbour_positions]:
                neighbour_positions += decohere_invalid_state(wf, pos, recurse - 1)

        return neighbour_positions

    def constrain_region(
        wf: WaveFunction, neighbour_positions: list[Pos]
    ) -> tuple[StateVec | None, StateResolutionError | None]:
        # Constrain the new states according to their neighbour states
        try:
            for pos in neighbour_positions:
                wf.states[pos.idx()].constrain(wf)
            return wf.get_next(), None
        except StateResolutionError as e:
            return None, e

    attempt = 0
    iteration = 0
    while result := _robust_iterator(wave_function, current_pos):
        next_vec, error = result

        # If nothing is returned, then iteration is complete and the wavefunction has collapsed
        if next_vec is None:
            break

        # if we couldn't resolve state, begin decohere-constrain loop on expanding region
        while error is not None and attempt < max_retries:
            if DEBUG:
                print(f"BACKTRACKING: {iteration=} {attempt=}, {error=}")
            to_constrain = decohere_invalid_state(wave_function, next_vec.pos, attempt)
            attempt += 1

            # loop will break on None or continue on error from constrain_region
            candidate, error = constrain_region(wave_function, to_constrain)
            if error:
                # this triggers another retry
                continue
            else:
                next_vec = candidate

            # if there's no error, we can move on
            next_vec = wave_function.get_next()

        # if we get here and there's still an error, we give up.
        if error is not None:
            # Backtracking has reached maximum attempts and has failed to collapse the wavefunction without contradiction
            if DEBUG:
                print(f"FAILED: {attempt=}, {error=}")
            raise IrreconcilableStateError.create(wave_function)

        # This iteration was successful, on to the next!
        iteration += 1
        attempt = 0

        # Check the next_vec after backtracking because backtracking can result in complete collapse of the wavefunction
        if next_vec is None:
            break

        # we have a non-null next vec so set a new current position and iterate again.
        current_pos = next_vec.pos

    # This is deterministic in the event that the above loop breaks without error (i.e. there's only one choice of state)
    return wave_function.choose_state()
