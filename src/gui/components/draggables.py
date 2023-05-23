from __future__ import annotations

from typing import TYPE_CHECKING

import arcade
from pyglet.math import Vec2

from src.utils.rectangle import Rectangle

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem
    from src.entities.gear.gear import Gear
    from src.gui.components.receivers import InventoryGrid


class Draggable:
    sprite: arcade.Sprite
    is_held: bool = False
    item: EquippableItem
    hit_box: Rectangle

    def __init__(self, item: EquippableItem, is_held=False):
        self.sprite = item._sprite.sprite
        self.item = item
        self.is_held = is_held

    @property
    def hit_box(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=Vec2(
                self.sprite.center_x - self.sprite.width / 2,
                self.sprite.center_y - self.sprite.height / 2,
            ),
            max_v=Vec2(
                self.sprite.center_x + self.sprite.width / 2,
                self.sprite.center_y + self.sprite.height / 2,
            ),
        )

    def is_clicked(self, mouse: tuple[int, int]) -> bool:
        return Vec2(*mouse) in self.hit_box

    def reposition(self, new_pos: Vec2):
        self.sprite.position = new_pos


class DraggableCollection:
    draggables: list[Draggable]
    hand: Draggable | None
    sprites: arcade.SpriteList
    inventory_grid: InventoryGrid

    def __init__(self, gear: Gear, inventory_grid: InventoryGrid) -> None:
        self.gear = gear
        self.inventory_grid = inventory_grid
        self.sprites = arcade.SpriteList()
        self.draggables = []
        self.prepare_draggables(gear)

        self.hand = None
        self.original_position = None

    def rescale_sprite(self, scale):
        self.hand.sprite.scale = scale
    
    def draggable_at_position(self, mouse_position: Vec2) -> Draggable | None:
        hovered_draggable = None

        for draggable in self.draggables:
            if mouse_position in draggable.hit_box:
                hovered_draggable = draggable
                break

        return hovered_draggable

    def prepare_draggables(self, gear: Gear):
        for item in gear.as_list():
            self.add_to_collection(Draggable(item))

        for draggable in self.inventory_grid.build_draggables():
            self.add_to_collection(draggable)

    def add_to_collection(self, draggable: Draggable):
        if draggable.sprite not in self.sprites:
            self.draggables.append(draggable)
            self.sprites.append(draggable.sprite)

    def pick_up_at_mouse(self, mouse: tuple[int, int]) -> tuple[int, int] | None:
        for item in self.draggables:
            item.is_held = not self.hand and item.is_clicked(mouse)
            if item.is_held:
                self.draggables.remove(item)
                self.hand = item
                self.rescale_sprite(12)
                return item.sprite.position

        return None

    def on_update(self, lmb: bool):
        if self.hand and not lmb:
            self.drop()

    def drop(self):
        self.draggables.append(self.hand)
        self.rescale_sprite(6)
        self.hand.is_held = False
        self.on_drop(self.hand)
        self.hand = None

    def on_drop(self, dropped: Draggable):
        pass
