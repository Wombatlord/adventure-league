from __future__ import annotations

import math
import operator
from typing import Generator, NamedTuple


class Node(NamedTuple):
    x: int | float
    y: int | float
    z: int | float = 0

    @property
    def east(self) -> Node:
        return Node(x=self.x + 1, y=self.y, z=self.z)

    @property
    def west(self) -> Node:
        return Node(x=self.x - 1, y=self.y, z=self.z)

    @property
    def north(self) -> Node:
        return Node(x=self.x, y=self.y + 1, z=self.z)

    @property
    def south(self) -> Node:
        return Node(x=self.x, y=self.y - 1, z=self.z)

    @property
    def above(self) -> Node:
        return Node(x=self.x, y=self.y, z=self.z + 1)

    @property
    def below(self) -> Node:
        return Node(x=self.x, y=self.y, z=self.z - 1)

    def distance_to(self, other: Node) -> float:
        return (self - other).mag()

    def mag(self) -> float:
        return math.sqrt(sum(coord**2 for coord in self))

    @property
    def adjacent(self) -> Generator[Node]:
        return self.get_adjacent()

    def get_adjacent(
        self, include_diag=True, three_d=False
    ) -> Generator[Node, None, None]:
        no_move = lambda n: n
        traversals_ns = (
            lambda n: n.north,
            no_move,
            lambda n: n.south,
        )
        traversals_ew = (
            lambda n: n.east,
            no_move,
            lambda n: n.west,
        )
        traversals_ud = (
            (
                lambda n: n.above,
                no_move,
                lambda n: n.below,
            )
            if three_d
            else (no_move,)
        )  # just stay in the plane if not 3d

        if not include_diag:
            # just move one node in + and - in each direction (east-west, north-south, up-down if relevant)
            yield from (
                move(self)
                for move in traversals_ud + traversals_ns + traversals_ew
                if move != no_move
            )
        else:
            # create the full set of 3x3 above and below plus the in-plane movements
            yield from (
                ns_move(ew_move(ud_move(self)))
                for ns_move in traversals_ns  # north and south traversals
                for ew_move in traversals_ew  # east and west traversals
                for ud_move in traversals_ud  # this includes above and below if three_d
                if (ns_move, ew_move, ud_move)
                != (no_move, no_move, no_move)  # exclude self from adjacent
            )

    def __eq__(self, other: Node) -> bool:
        if not isinstance(other, Node):
            return False

        return self.x == other.x and self.y == other.y and self.z == other.z

    def __sub__(self, other: Node) -> Node:
        if not isinstance(other, Node):
            raise TypeError(f"Expected a node, got: {other=}")
        return Node(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other: Node) -> Node:
        if not isinstance(other, Node):
            raise TypeError(f"Expected a node, got: {other=}")
        return Node(self.x + other.x, self.y + other.y, self.z + other.z)
