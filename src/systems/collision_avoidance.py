from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.engine import Engine

from src.entities.dungeon import Room


class SpaceOccupancyHandler:
    current_room: Room | None

    def __init__(self, eng: Engine):
        self.current_room = None
        eng.projection_dispatcher.static_subscribe(
            topic="new_encounter",
            handler_id=f"{self.__class__.__name__}.handle_new_encounter",
            handler=self.handle_new_encounter,
        )
        eng.projection_dispatcher.static_subscribe(
            topic="cleanup",
            handler_id=f"{self.__class__.__name__}.handle_cleanup",
            handler=self.handle_cleanup,
        )
        eng.projection_dispatcher.static_subscribe(
            topic="move",
            handler_id=f"{self.__class__.__name__}.handle_move",
            handler=self.handle_move,
        )

    def handle_new_encounter(self, event: dict):
        self.current_room = event.get("new_encounter")
        assert self.current_room is not None

    def handle_cleanup(self, _: dict):
        self.current_room = None

    def handle_move(self, _: dict):
        self.current_room.update_pathing_obstacles()
