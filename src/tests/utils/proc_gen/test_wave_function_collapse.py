from typing import Callable, NamedTuple, Self
from unittest import TestCase

from parameterized import parameterized

from src.utils.proc_gen.wave_function_collapse import (
    EAST,
    SOUTH,
    CollapseResult,
    IrreconcilableStateError,
    Observation,
    Pos,
    Side,
    StateVec,
    config,
    from_distribution,
    generate,
    iter_one_from,
    iterate_with_backtracking,
)


class PathTile(NamedTuple):
    north: bool = False
    east: bool = False
    south: bool = False
    west: bool = False

    def __str__(self) -> str:
        return char_map[self]

    @classmethod
    def all(cls) -> list[Self]:
        return [PathTile(*[(j >> i) % 2 == 0 for i in range(4)]) for j in range(16)]

    def compatibilities(self, side: Side) -> set[Observation]:
        # all possible states
        all_states = self.all()

        # filter down to just the ones that make sense next to this one
        return {state for state in all_states if self[side] == state[side.opposite()]}


char_map = dict(zip(reversed(PathTile.all()), " │─└││┌├─┘─┴┐┤┬┼"))


def constrained_path_tiling():
    dist = {s: 1 for s in PathTile.all()}
    dist[PathTile()] = 2
    dist[PathTile(north=True, east=True, west=True)] = 0
    dist[PathTile(south=True, east=True, west=True)] = 0
    dist[PathTile(north=True, south=True, west=True)] = 0
    dist[PathTile(north=True, east=True, south=True)] = 0
    dist[PathTile(north=True, east=True, west=True, south=True)] = 0
    dist[PathTile(north=True)] = 0
    dist[PathTile(south=True)] = 0
    dist[PathTile(east=True)] = 0
    dist[PathTile(west=True)] = 0

    # disallow horizontal lines
    dist[PathTile(east=True, west=True)] = 0
    dist[PathTile(north=True, south=True)] = 0

    factory = from_distribution(dist)

    try:
        result = iterate_with_backtracking(iter_one_from, factory)
    except IrreconcilableStateError:
        raise

    result = [*result.values()]


class HeightTile(NamedTuple):
    height: int

    def __str__(self) -> str:
        return f"{self.height}"

    @classmethod
    def all(cls) -> list[Self]:
        return [HeightTile(i) for i in range(10)]

    def compatibilities(self, side: Side) -> set[Observation]:
        compatible_heights = (-1, 0, 1)

        return {HeightTile(self.height + i) for i in compatible_heights}


def height_map(width: int = 10, height: int = 10) -> CollapseResult:
    config.set_dims(width, height)
    dist = {HeightTile(i): 1 for i in range(10)}

    factory = from_distribution(dist)

    try:
        result = generate(factory)
    except IrreconcilableStateError:
        raise

    return result


class CollapseStressTest(TestCase):
    @parameterized.expand(
        [
            ("height map", height_map, 90),
            ("constrained path tiling", constrained_path_tiling, 90),
        ]
    )
    def test_stress_collapse(
        self, name: str, run_one: Callable[[], None], min_percent: int
    ):
        results = {"success": 0, "fail": 0}

        while results["success"] + results["fail"] < 50:
            try:
                run_one()
                results["success"] += 1
            except IrreconcilableStateError:
                results["fail"] += 1

        attempts = results["success"] + results["fail"]
        success_percent = int(results["success"] / attempts * 100)

        assert (
            success_percent > min_percent
        ), f"{name=} success rate was {success_percent}%, expected above {min_percent}%"
