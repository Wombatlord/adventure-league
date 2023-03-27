import unittest

from parameterized import parameterized

from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


def gated_wall(gap: int, v_pos: int, wall_len: int) -> set[Node]:
    """
    returns a representation of a horizontal wall with a gap at some
    position labelled by the gap parameter. The v_pos expresses the
    vertical position of the wall (zero at the bottom) and the wall_len
    expresses how many cells wide the wall is from left to right with
    the first position in the wall always being x=0 at the left.
    """
    return {Node(x=x, y=v_pos) for x in {*range(wall_len)} - {gap}}


width, height = 10, 10


class TestPathing(unittest.TestCase):
    # this decorator runs the test for every args tuple supplied, in this case it's width*(height - 2) different
    # inputs. Being this exhaustive is probably unnecessary so if it's slow, it could be restricted to a fixed gap
    # position or something.
    @parameterized.expand(
        [
            (gap, wall_v_pos)
            for gap in range(width)  # gap can be anywhere in the wall
            for wall_v_pos in range(
                1, height - 1
            )  # wall can be any height except covering start or finish
        ]
    )
    def test_path_respects_obstructions(self, gap: int, wall_v_pos: int) -> None:
        """
        This test is specifically concerned with ensuring that the space in which
        to do pathing, expressed in terms of the bottom left and top right corners
        of a rectangle and the places within the rectangle that are inaccessible
        to pathing, behaves as expected with respect to the paths it produces

        :param int gap: This is the horizontal position of the only gap in the wall that the path must pass through,
        zero on the left
        :param int wall_v_pos: The vertical position of the wall, zero at the bottom
        """

        # Arrange
        # construct the set of excluded nodes
        wall = gated_wall(gap, wall_v_pos, width)

        # construct the space in which to find paths with the wall passed
        # as the exclusions
        space = PathingSpace(
            minima=Node(x=0, y=0),
            maxima=Node(x=10, y=10),
            exclusions=wall,
        )

        start_at = space.minima  # bottom left
        end_at = space.maxima.south.west  # top right (those semantics tho...)

        # Action
        # ask the pathing interface for a path
        path = [*space.astar(start_at, end_at)]

        # Assert
        # we're using set intersection to interrogate the overlap (if any),
        # the overlap is the intersection of the set of wall nodes and the set of path nodes
        actual_overlap = {*path} & wall

        # we expect the overlap to be the empty set, a.k.a if the wall occupies a Node, the path doesn't use it
        expected_overlap = set()

        # check they are the same
        assert (
            actual_overlap == expected_overlap
        ), f"The path ignored the obstruction, the overlap with the wall was {actual_overlap=}"

        # Check the path does in fact include the start and the end
        assert (
            start_at in path
        ), f"The path did not include the starting location {start_at=}. Full path: {path=}"

        assert (
            end_at in path
        ), f"The path did not include intended destination {end_at=}. Full path: {path=}"


class TestConstructFromLevelGeometry(unittest.TestCase):
    def get_trivial_level(self) -> tuple[Node]:
        return (Node(0, 0, -1),)

    def get_geometry_with_blocked_nodes(
        self, blocked_nodes: set[Node], size: tuple[int, int]
    ) -> tuple[Node, ...]:
        return tuple(
            [Node(x, y, z=-1) for x in range(0, size[0]) for y in range(0, size[1])]
            + list(blocked_nodes)
        )

    def get_geometry_with_holes_in_floor(
        self, hole_locations: set[Node], size: tuple[int, int]
    ) -> tuple[Node, ...]:
        return tuple(
            (
                {Node(x, y, z=-1) for x in range(0, size[0]) for y in range(0, size[1])}
                - hole_locations
            )
        )

    def test_from_level_geometry_creates_single_node_from_trivial_level(self):
        # Arrange
        geom = self.get_trivial_level()

        # Action
        space = PathingSpace.from_level_geometry(geom)

        # Assert
        assert len(space) == 1
        assert Node(0, 0, 0) in space

    def test_from_level_geometry_creates_exclusions_for_blocked_nodes(self):
        # Arrange
        blocked = {Node(1, 1), Node(3, 2), Node(0, 4)}
        geom = self.get_geometry_with_blocked_nodes(blocked, size=(5, 5))

        # Action
        space = PathingSpace.from_level_geometry(geom)

        # Assert
        assert (
            len(space.exclusions) == 3
        ), f"unexpected number of exclusions, expected 3, got {len(space.exclusions)=}"
        assert (
            space.exclusions == blocked
        ), f"blocked nodes {blocked=}, exclusions in the wrong place {space.exclusions-blocked}"

    def test_from_level_geometry_creates_exclusions_for_when_nodes_are_above_pits(self):
        # Arrange
        pit_locations = {Node(1, 1, z=-1), Node(3, 2, z=-1), Node(0, 4, z=-1)}
        geom = self.get_geometry_with_holes_in_floor(pit_locations, size=(5, 5))

        # Action
        space = PathingSpace.from_level_geometry(geom)

        # Assert
        assert (
            len(space.exclusions) == 3
        ), f"unexpected number of exclusions, expected 3, got {len(space.exclusions)=}"

        expected_exclusions = {n.above for n in pit_locations}
        assert space.exclusions == expected_exclusions, (
            f"excluded nodes {expected_exclusions=}, exclusions in the wrong place:"
            f" {space.exclusions-expected_exclusions}"
        )
