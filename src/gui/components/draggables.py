from __future__ import annotations

from typing import TYPE_CHECKING

import arcade

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem
    from src.entities.gear.gear import Gear
    from src.gui.components.receivers import InventoryGrid


class Draggable:
    sprite: arcade.Sprite
    is_held: bool = False
    item: EquippableItem

    def __init__(self, item: EquippableItem, is_held=False):
        self.sprite = item._sprite.sprite
        self.item = item
        self.is_held = is_held

    def is_clicked(self, mouse: tuple[int, int]) -> bool:
        return self.sprite.collides_with_point(mouse)


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

    def prepare_draggables(self, gear: Gear):
        for item in gear.as_list():
            self.add_to_collection(Draggable(item))

        for draggable in self.inventory_grid.build_draggables():
            self.add_to_collection(draggable)

    def add_to_collection(self, draggable: Draggable):
        if draggable.sprite not in self.sprites:
            self.draggables.append(draggable)
            self.sprites.append(draggable.sprite)

    def pick_up_at_mouse(self, mouse: tuple[int, int]):
        for item in self.draggables:
            item.is_held = not self.hand and item.is_clicked(mouse)
            if item.is_held:
                self.draggables.remove(item)
                self.hand = item
                return

    def on_update(self, lmb: bool):
        if self.hand and not lmb:
            self.drop()

    def drop(self):
        self.draggables.append(self.hand)
        self.hand.is_held = False
        self.on_drop(self.hand)
        self.hand = None

    def on_drop(self, dropped: Draggable):
        pass
