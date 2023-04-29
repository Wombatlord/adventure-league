from typing import Generator, NamedTuple

from pyglet.math import Vec3

from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class Ray(NamedTuple):
    start: Node

    def cast(self, look_at: Node) -> Generator[Node, None, None]:
        if self.start == look_at:
            raise ValueError(
                f"The target for the ray {look_at=} is the same as the start point {self.start=}. "
                f"Two distinct points are required"
            )

        rect = look_at - self.start

        # We want to step in increments of 1 along the longest side of the
        # area that bounds the ray, this means we will always increment
        # the other components by less than 1
        divisor = max(abs(component) for component in rect)
        if divisor == 0:
            return

        step = Vec3(*rect) / divisor
        curr_vec = Vec3(0, 0, 0)
        while True:
            next_node = Node(
                x=round(curr_vec.x),
                y=round(curr_vec.y),
                z=round(curr_vec.z),
            )

            yield next_node + self.start
            curr_vec = curr_vec + step

    def segment(self, stop: Node) -> list[Node]:
        seg = []
        for pt in self.cast(stop):
            seg.append(pt)
            if pt == stop:
                # if the last pt we appended was stop
                break

        return seg

    def line_of_sight(self, space: PathingSpace, look_at: Node) -> list[Node]:
        los = []
        for point in self.cast(look_at):
            if not space.is_pathable(point):
                break
            los.append(point)

        return los
