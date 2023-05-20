from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

import arcade
from arcade.gui.widgets.text import UILabel

from src.engine.armory import Armory
from src.entities.combat.fighter import Fighter
from src.entities.gear.equippable_item import EquippableItem
from src.gui.components.buttons import nav_button
from src.gui.generic_sections.command_bar import CommandBarSection
from src.gui.guild.inventory_grid import GridLoc, SnapGrid

if TYPE_CHECKING:
    from src.entities.gear.gear import Gear

from src.engine.init_engine import eng
from src.gui.generic_sections.info_pane import InfoPaneSection
from src.gui.window_data import WindowData
from pyglet.math import Vec2


class EquipView(arcade.View):
    """Draw a view displaying information about a guild"""

    def __init__(
        self, to_be_equipped: Fighter, parent_factory: Callable[[], arcade.View]
    ):
        super().__init__()
        self.parent_factory = parent_factory
        self.to_be_equipped = to_be_equipped
        # InfoPane config.
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=148,
            prevent_dispatch={False},
            prevent_dispatch_view={False},
            margin=5,
            texts=[
                UILabel(
                    text=self.to_be_equipped.owner.name.name_and_title,
                    font_size=24,
                    font_name=WindowData.font,
                )
            ],
        )

        # CommandBar config
        self.buttons = [
            nav_button(self.parent_factory, "Roster"),
        ]
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch={False},
            prevent_dispatch_view={False},
        )

        self.equip_section = EquipSection(
            left=0,
            bottom=198,
            width=WindowData.width,
            height=WindowData.height - 198,
            prevent_dispatch={False},
            prevent_dispatch_view={False},
            fighter=self.to_be_equipped,
        )

        # Add sections to section manager.
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)
        self.add_section(self.equip_section)

    def on_draw(self):
        self.clear()

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

        self.clear()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        pass


###################
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
    ):
        self._grid = SnapGrid.from_grid_dimensions(
            w, h, slot_size, bottom_left or Vec2(0, 0)
        )
        self._sprite_dims = slot_size * 0.8
        self._contents = contents or {}
        self._storage = storage
        self._gear = gear
    
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

    def put_into_slot_at_sprite(self, sprite: arcade.Sprite, item: EquippableItem) -> bool:
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


class EquipSection(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        fighter: Fighter,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)
        self.fighter = fighter
        self.gear = fighter.gear
        self.armory = eng.game_state.get_guild().armory

        self.item_receivers = ReceiverCollection(self.armory)
        self.inventory_grid = InventoryGrid(
            3,
            4,
            Vec2(60, 90),
            self.armory,
            self.gear,
            bottom_left=Vec2(0, 2 * self.height / 3),
        )
        self._register_receivers()

        self.draggable_collection = DraggableCollection(self.gear, self.inventory_grid)

        self.mouse = 0, 0
        self.lmb_pressed = False

        self.draggable = None
        self.original_draggable_position = None

    def get_original_pos(self):
        return self.original_draggable_position

    def _register_receivers(self):
        slot_x, slot_y = 900, 650
        for slot in ("_weapon", "_helmet", "_body"):
            self.item_receivers.register(
                slot=slot,
                receiver=ItemReceiver(
                    gear=self.gear,
                    slot=slot,
                    sprite=arcade.SpriteSolidColor(
                        width=50,
                        height=50,
                        color=arcade.csscolor.AQUAMARINE,
                        center_x=slot_x,
                        center_y=slot_y,
                    ),
                    inventory_grid=self.inventory_grid,
                ),
            )
            slot_y -= 150

        for receiver in self.inventory_grid.build_receivers():
            self.item_receivers.register_armory(receiver)

    def on_draw(self):
        self.item_receivers.sprites.draw(pixelated=True)
        self.draggable_collection.sprites.draw(pixelated=True)

    def on_update(self, dt: float):
        if self.draggable and self.draggable.is_held:
            self.draggable.sprite.position = self.mouse

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.mouse = x, y
        self.lmb_pressed = button == arcade.MOUSE_BUTTON_LEFT
        if self.lmb_pressed:
            for draggable in self.draggable_collection.draggables:
                if draggable.is_clicked(self.mouse):
                    draggable.is_held = True
                    self.draggable = draggable
                    self.original_draggable_position = self.draggable.sprite.position
                    return

    def _get_receiver_sprite(self, x: int, y: int) -> arcade.Sprite | None:
        """
        This currently requires an exact overlap of mouse position and ItemReceiver sprite
        """
        pos = (x, y)
        for sprite in self.item_receivers.sprites:
            if sprite.position == pos:
                return sprite

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if not self.draggable:
            return

        self.mouse = x, y
        if self.lmb_pressed and button == arcade.MOUSE_BUTTON_LEFT:
            self.lmb_pressed = False

            item_slot_sprite, distance = arcade.get_closest_sprite(
                self.draggable.sprite, self.item_receivers.sprites
            )

            successfully_placed = False
            if arcade.check_for_collision(self.draggable.sprite, item_slot_sprite):
                successfully_placed = self.item_receivers.put_into_slot_at_sprite(
                    item_slot_sprite, self.draggable.item
                )

            if not successfully_placed:
                self.draggable.sprite.position = self.original_draggable_position
            
            self.draggable.is_held = False
            self.draggable = None

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse = x, y

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.P:
            breakpoint()
