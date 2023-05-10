from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.engine import Engine

from src.world.level.room import Room


class SpaceOccupancyHandler:
    current_room: Room | None = None

    @classmethod
    def handle_new_encounter(cls, event: dict):
        cls.current_room = event.get("new_encounter")
        assert cls.current_room is not None

    @classmethod
    def handle_cleanup(cls, _: dict):
        cls.current_room = None

    @classmethod
    def handle_move(cls, _: dict):
        cls.current_room.update_pathing_obstacles()


def subscribe(eng: Engine):
    eng.projection_dispatcher.static_subscribe(
        topic="new_encounter",
        handler_id=f"{SpaceOccupancyHandler.__name__}.handle_new_encounter",
        handler=SpaceOccupancyHandler.handle_new_encounter,
    )
    eng.projection_dispatcher.static_subscribe(
        topic="cleanup",
        handler_id=f"{SpaceOccupancyHandler.__name__}.handle_cleanup",
        handler=SpaceOccupancyHandler.handle_cleanup,
    )
    eng.projection_dispatcher.static_subscribe(
        topic="move",
        handler_id=f"{SpaceOccupancyHandler.__name__}.handle_move",
        handler=SpaceOccupancyHandler.handle_move,
    )
