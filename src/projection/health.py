from __future__ import annotations

from typing import Any

import arcade

from src.entities.entity import Species
from src.gui.window_data import WindowData

_KEY = "entity_data"

_health_projection: dict[str, str] = {}


class HealthProjection:
    def __init__(self):
        self.config = {}

    def configure(
        self, team: list, heights: list[int] = None, **kwargs
    ) -> HealthProjection:
        self.config = kwargs
        self.heights = heights if heights else []
        self.names = [member.name.name_and_title for member in team]
        return self

    def draw(self) -> None:
        merc_heights = [*self.heights]
        enemy_heights = [*self.heights]
        for name, health in _health_projection.items():
            try:
                if name in self.names:
                    start_y = merc_heights.pop(0)
                else:
                    start_y = enemy_heights.pop(0)
            except IndexError:
                break
            if name in self.names:
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
                    **self.config,
                ).draw()
            else:
                arcade.Text(
                    text=f"{name}: {health}",
                    start_x=WindowData.width * 0.85,
                    start_y=start_y,
                    anchor_x="center",
                    anchor_y="center",
                    multiline=True,
                    width=500,
                    align="center",
                    color=arcade.color.RED_DEVIL,
                    font_name=WindowData.font,
                    **self.config,
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
    health = entity.get("health")
    retreat = entity.get("retreat")
    name = entity.get("name")
    species = entity.get("species", "human")
    if name is None:
        return

    formatted_name = ""
    if species == Species.HUMAN:
        formatted_name = name
    else:
        formatted_name = f"{species.capitalize()}: {name}"

    _update_projection(health, formatted_name, retreat)


def _update_projection(health: int, formatted_name: str, retreat: bool):
    if health is None:
        return

    # The actual projection logic
    if retreat == False:
        _health_projection[formatted_name] = f"{health}" if health > 0 else "dead"

    if retreat or health <= 0:
        # Ensure we don't try to clear the projection twice if the entity
        # is killed during its retreat.
        if formatted_name in _health_projection:
            _health_projection.pop(formatted_name)


def flush_handler(event):
    flush()
