from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import arcade

from src.engine.armory import Armory
from src.gui.components.draggables import Draggable
from src.gui.guild.snap_grid import SnapGrid
from src.textures.pixelated_nine_patch import PixelatedNinePatch
from src.textures.texture_data import SingleTextureSpecs
from src.utils.rectangle import Corner, Rectangle

if TYPE_CHECKING:
    from src.entities.gear.equippable_item import EquippableItem
    from src.gui.guild.snap_grid import GridLoc
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

    def put(self, draggable: Draggable) -> bool:
        if not self.can_receive(draggable):
            return False
        if not self.gear.is_equipped(draggable.item):
            self.inventory_grid.take(draggable, remove_from_storage=True)
            self.gear.equip_item(draggable.item, eng.game_state.guild.armory)

        draggable.item._sprite.sprite.position = self.sprite.position
        return True

    def can_receive(self, draggable: Draggable) -> bool:
        return draggable.item.slot == self.slot

    def initial_overlay(self):
        if self.slot == "_weapon" and self.gear.weapon:
            self.gear.weapon._sprite.sprite.position = self.sprite.position
        elif self.slot == "_helmet" and self.gear.helmet:
            self.gear.helmet._sprite.sprite.position = self.sprite.position
        elif self.slot == "_body" and self.gear.body:
            self.gear.body._sprite.sprite.position = self.sprite.position

    def reposition(self, new_pos: Vec2):
        self.sprite.position = new_pos


class InventoryGrid:
    _grid: SnapGrid
    _contents: dict[GridLoc, Draggable]

    def __init__(
        self,
        w: int,
        h: int,
        slot_size: Vec2,
        storage: Armory,
        gear: Gear,
        bottom_left: Vec2 | None = None,
        contents: dict[GridLoc, Draggable] | None = None,
    ):
        self._grid = SnapGrid.from_grid_dimensions(
            w, h, slot_size, bottom_left or Vec2(0, 0)
        )
        self._sprite_dims = slot_size * 0.9
        self._contents = contents or {}
        self._storage = storage
        self._gear = gear
        self._pin_args = None
        self._receivers = []
        self._draggables = []

    def get_bounds(self) -> Rectangle:
        return self._grid.bounds

    def search_contents(self, draggable: Draggable) -> GridLoc | None:
        for loc, candidate in self._contents.items():
            if draggable.item is candidate.item:
                return loc

        return None

    def pin_corner(self, corner: Corner, pin: Callable[[], Vec2]):
        self._grid.pin_corner(corner, pin)

    def on_resize(self):
        self._grid.on_resize()

        for receiver, screen_pos in zip(
            self._receivers, self._grid.locations_in_rows()
        ):
            grid_loc = self._grid.to_grid_loc(screen_pos)
            if occupying_draggable := self._contents.get(grid_loc):
                occupying_draggable.reposition(screen_pos)
            receiver.reposition(screen_pos)

    def take(self, draggable: Draggable, remove_from_storage: bool = False):
        item = draggable.item
        loc = self.search_contents(draggable)
        if loc:
            self._contents.pop(loc)
        if item in self._storage and remove_from_storage:
            self._storage.remove(item)

    def put(self, draggable: Draggable):
        item = draggable.item
        screen_pos = Vec2(*item.sprite.sprite.position)

        snapped = self._grid.snap_to_grid(screen_pos)
        if snapped is None:
            return

        item.sprite.sprite.position = snapped

        if item in self._storage.storage:
            self.take(draggable)
        elif self._gear.is_equipped(item):
            self._gear.unequip(item.slot, self._storage)

        self._contents[self._grid.to_grid_loc(screen_pos)] = draggable

    def build_receivers(self) -> list[StorageReceiver]:
        if self._receivers:
            return [*self._receivers]

        for screen_pos in self._grid.locations_in_rows():
            self._receivers.append(self._build_receiver(screen_pos))

        return [*self._receivers]

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
            draggable = self._build_draggable(screen_pos, storage[placed])
            draggables.append(draggable)
            placed += 1
            self._contents[self._grid.to_grid_loc(screen_pos)] = draggable
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

    def put(self, draggable: Draggable) -> bool:
        if not self.can_receive(draggable):
            return False

        self.inventory_grid.put(draggable)
        return True

    def can_receive(self, draggable: Draggable) -> bool:
        return not self.inventory_grid.is_occupied(
            Vec2(*draggable.item.sprite.sprite.position)
        )

    def reposition(self, new_pos: Vec2):
        self.sprite.position = new_pos


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
        self, sprite: arcade.Sprite, draggable: Draggable
    ) -> bool:
        slot = self.identify_equip_slot(sprite)
        if not slot:
            slot = self.identify_inventory_slot(sprite)

        if slot is None:
            raise ValueError("Could not identify slot")

        match slot:
            case x if isinstance(x, str):
                if receiver := self._item_receivers.get(slot, None):
                    return receiver.put(draggable)
            case x if isinstance(x, int):
                return self._storage_receivers[slot].put(draggable)
