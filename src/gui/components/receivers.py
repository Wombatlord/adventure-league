from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import arcade

from src.engine.armory import Armory
from src.gui.components.draggables import Draggable
from src.gui.guild.inventory_grid import SnapGrid

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem
    from src.gui.guild.inventory_grid import GridLoc
    from src.entities.gear.gear import Gear

from pyglet.math import Vec2

from src.engine.init_engine import eng


class ItemReceiver:
    def __init__(
        self,
        gear: Gear,
        slot: str,
        sprite: arcade.Sprite,
        inventory_grid: InventoryGrid,
    ):
        self.inventory_grid = inventory_grid
        self.gear = gear
        self.slot = slot
        self.sprite = sprite
        self.initial_overlay()

    def put(self, item: EquippableItem) -> bool:
        if not self.can_receive(item):
            return False
        if not self.gear.is_equipped(item):
            self.inventory_grid.take(item)
            self.gear.equip_item(item, eng.game_state.guild.armory)

        item._sprite.sprite.position = self.sprite.position
        return True

    def can_receive(self, item) -> bool:
        return item.slot == self.slot

    def initial_overlay(self):
        if self.slot == "_weapon" and self.gear.weapon:
            self.gear.weapon._sprite.sprite.position = self.sprite.position
        elif self.slot == "_helmet" and self.gear.helmet:
            self.gear.helmet._sprite.sprite.position = self.sprite.position
        elif self.slot == "_body" and self.gear.body:
            self.gear.body._sprite.sprite.position = self.sprite.position


class InventoryGrid:
    def __init__(
        self,
        w: int,
        h: int,
        slot_size: Vec2,
        storage: Armory,
        gear: Gear,
        bottom_left: Vec2 | None = None,
        contents: dict[GridLoc, EquippableItem] | None = None,
        original_draggable_position: Callable[[], tuple[float, float] | None]
        | None = None,
    ):
        self._grid = SnapGrid.from_grid_dimensions(
            w, h, slot_size, bottom_left or Vec2(0, 0)
        )
        self._sprite_dims = slot_size * 0.8
        self._contents = contents or {}
        self._storage = storage
        self._gear = gear
        self.original_draggable_position = original_draggable_position

    def search_contents(self, item) -> GridLoc | None:
        for loc, candidate in self._contents.items():
            if item is candidate:
                return loc

        return None

    def take(self, item: EquippableItem):
        loc = self.search_contents(item)
        if loc:
            self._contents.pop(loc)
        if item in self._storage:
            self._storage.remove(item)

    def put(self, item: EquippableItem):
        screen_pos = Vec2(*item.sprite.sprite.position)

        snapped = self._grid.snap_to_grid(screen_pos)
        if snapped is None:
            item.sprite.sprite.position = self.original_draggable_position()
            return

        item.sprite.sprite.position = snapped

        if self._gear.is_equipped(item):
            self._gear.unequip(item.slot, self._storage)
        else:
            self.take(item)

        self._contents[self._grid.to_grid_loc(screen_pos)] = item

    def build_receivers(self) -> list[StorageReceiver]:
        receivers = []
        for screen_pos in self._grid.locations_in_rows():
            receivers.append(self._build_receiver(screen_pos))

        return receivers

    def _build_receiver(self, screen_pos: Vec2) -> StorageReceiver:
        return StorageReceiver(
            arcade.SpriteSolidColor(
                width=self._sprite_dims.x,
                height=self._sprite_dims.y,
                center_x=screen_pos.x,
                center_y=screen_pos.y,
                color=arcade.color.GRAY,
            ),
            self,
        )

    def build_draggables(self) -> list[Draggable]:
        draggables = []
        storage = self._storage.storage
        placed = 0
        for screen_pos in self._grid.locations_in_rows():
            if placed >= len(storage):
                continue

            item = storage[placed]
            draggables.append(self._build_draggable(screen_pos, storage[placed]))
            placed += 1
            self._contents[self._grid.to_grid_loc(screen_pos)] = item
            item.sprite.sprite.position = screen_pos

        return draggables

    def _build_draggable(self, screen_pos: Vec2, item: EquippableItem) -> Draggable:
        item.sprite.position = screen_pos.x, screen_pos.y
        return Draggable(item)

    def is_occupied(self, screen_pos: Vec2) -> bool:
        loc = self._grid.to_grid_loc(screen_pos)
        return loc in self._contents


class StorageReceiver:
    def __init__(self, sprite: arcade.Sprite, inventory: InventoryGrid):
        self.sprite = sprite
        self.inventory_grid = inventory

    def put(self, item: EquippableItem) -> bool:
        if not self.can_receive(item):
            return False

        self.inventory_grid.put(item)
        return True

    def can_receive(self, item: EquippableItem) -> bool:
        return not self.inventory_grid.is_occupied(Vec2(*item.sprite.sprite.position))


class ReceiverCollection:
    _item_receivers: dict[str, ItemReceiver]

    def __init__(self, storage: Armory):
        self.storage = storage
        self._item_receivers = {}
        self._storage_receivers = []
        self.sprites = arcade.SpriteList()

    def register(self, slot: str, receiver: ItemReceiver):
        self._item_receivers[slot] = receiver
        if receiver.sprite not in self.sprites:
            self.sprites.append(receiver.sprite)

    def register_armory(self, reciever: StorageReceiver):
        if reciever.sprite in self.sprites:
            return
        self._storage_receivers.append(reciever)
        self.sprites.append(reciever.sprite)

    def identify_equip_slot(self, sprite: arcade.Sprite) -> str | None:
        items = self._item_receivers.items()

        for slot, receiver in items:
            if receiver.sprite is sprite:
                return slot

        return None

    def identify_inventory_slot(self, sprite: arcade.Sprite) -> int | None:
        for slot, receiver in enumerate(self._storage_receivers):
            if receiver.sprite is sprite:
                return slot

        return None

    def put_into_slot_at_sprite(
        self, sprite: arcade.Sprite, item: EquippableItem
    ) -> bool:
        slot = self.identify_equip_slot(sprite)
        if not slot:
            slot = self.identify_inventory_slot(sprite)

        if slot is None:
            raise ValueError("Could not identify slot")

        match slot:
            case x if isinstance(x, str):
                if receiver := self._item_receivers.get(slot, None):
                    return receiver.put(item)
            case x if isinstance(x, int):
                return self._storage_receivers[slot].put(item)
