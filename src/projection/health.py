from __future__ import annotations
from typing import Any
from src.gui.window_data import WindowData
import arcade

_KEY = "entity_data"

_health_projection: dict[str, str] = {}

class HealthProjection:
    def __init__(self):
        self.config = {}

    def configure(self, heights: list[int] = None, **kwargs) -> HealthProjection:
        self.config = kwargs
        self.heights = heights if heights else []
        return self
    
    def draw(self) -> None:
        heights = [*self.heights]

        for name, health in _health_projection.items():
            try:
                start_y = heights.pop(0)
            except IndexError:
                break

            arcade.Text(
                text=f"{name}: {health}",
                start_x=WindowData.width / 8,
                start_y=start_y,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=500,
                align="center",
                color=arcade.color.AIR_SUPERIORITY_BLUE,
                font_name=WindowData.font,
                **self.config
            ).draw()

def current() -> HealthProjection:
    return HealthProjection()

def flush() -> None:
    """
    This should re-initialise the projection to its state on import of this module
    """
    global _health_projection
    _health_projection = {}

def consume(action: dict[str, Any]) -> None:
    """
    This will be invoked by the action queue
    """
    entity = action.get(_KEY, {})
    retreat = entity.get("retreat")
    name = entity.get("name")
    if name is None:
        return

    health = entity.get("health")
    if health is None:
        return

    # The actual projection logic
    if retreat == False:
        _health_projection[name] = f"{health}" if health > 0 else "dead"
        
    if retreat or health <= 0:
        # Ensure we don't try to clear the projection twice if the entity
        # is killed during its retreat.
        if name in _health_projection:
            _health_projection.pop(name)

def get_subscription() -> set[str]:
    """
    registers this module as a consumer of events with the returned keys present
    """
    return {_KEY}