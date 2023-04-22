from typing import Generator, NamedTuple

from pyglet.math import Vec3

from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace


class Ray(NamedTuple):
    start: Node

    def cast(self, look_at: Node) -> Generator[Node, None, None]:
        rect = look_at - self.start

        curr_vec = Vec3(0, 0, 0)
        step = Vec3(1, rect.y / rect.x, rect.z / rect.x)

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
            if point in space.static_exclusions:
                break
            los.append(point)

        return los
