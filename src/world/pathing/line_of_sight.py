from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace
from src.world.ray import Ray


def line_of_sight(space: PathingSpace, eye: Ray, look_at: Node) -> list[Node]:
    los = []
    for point in eye.cast(look_at):
        if point in space.static_exclusions:
            break
        los.append(point)

    return los
