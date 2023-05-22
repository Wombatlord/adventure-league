from __future__ import annotations

import math
from copy import copy
from typing import TYPE_CHECKING, Callable

import arcade
from arcade.gui.widgets.text import UILabel

from src.engine.armory import Armory
from src.entities.combat.fighter import Fighter
from src.entities.gear.equippable_item import EquippableItem
from src.gui.components.buttons import nav_button
from src.gui.components.draggables import DraggableCollection
from src.gui.components.observer import Observer, observe
from src.gui.components.receivers import InventoryGrid, ItemReceiver, ReceiverCollection
from src.gui.generic_sections.command_bar import CommandBarSection
from src.gui.guild.snap_grid import GridLoc, SnapGrid
from src.textures.pixelated_nine_patch import PixelatedNinePatch
from src.textures.texture_data import SingleTextureSpecs
from src.utils.rectangle import Corner, Rectangle

if TYPE_CHECKING:
    from src.entities.gear.gear import Gear

from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.gui.generic_sections.info_pane import InfoPaneSection
from src.gui.window_data import WindowData


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
                ),
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

    def on_update(self, delta_time: float):
        self.to_be_equipped.owner.entity_sprite.sprite.update_animation(delta_time)

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

        self.to_be_equipped.owner.entity_sprite.sprite.set_scale(16)
        self.to_be_equipped.owner.entity_sprite.sprite.position = (
            self.window.width * 0.7,
            self.window.height * 0.8,
        )

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

        self.to_be_equipped.owner.entity_sprite.sprite.set_scale(4)

        self.clear()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        pass


def sync_item_info(equipment_text: arcade.Text, item: EquippableItem | None) -> None:
    if item is None:
        equipment_text.text = "No stats to display."
        return

    equipment_text.text = item.display_stats()


def equipment_hover_text(
    get_item: Callable[[], EquippableItem | None], position: Vec2
) -> arcade.Text:
    observer = observe(
        get_observed_state=get_item,
        sync_widget=sync_item_info,
    )

    hovered_item_info = arcade.Text(
        text="",
        start_x=position.x,
        start_y=position.y,
        font_name=WindowData.font,
        font_size=18,
        anchor_x="center",
    )
    sync_item_info(hovered_item_info, get_item())

    return observer.attach(hovered_item_info)


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
            7,
            8,
            Vec2(60, 60),
            self.armory,
            self.gear,
            bottom_left=Vec2(15, self.height - 300),
        )

        top_left_offset = self.inventory_grid.get_bounds().corners[
            Corner.TOP_LEFT.value
        ] - (Vec2(0, self.get_height()) + self.get_position())
        self.inventory_grid.pin_corner(
            Corner.TOP_LEFT,
            lambda: Vec2(0, self.get_height()) + self.get_position() + top_left_offset,
        )
        self._register_receivers()

        self.draggable_collection = DraggableCollection(self.gear, self.inventory_grid)

        self.mouse = 0, 0
        self.lmb_pressed = False

        self.original_draggable_position = None
        self.grid_backing = PixelatedNinePatch(
            left=16,
            right=16,
            bottom=16,
            top=16,
            texture=SingleTextureSpecs.panel_highlighted.loaded,
        )
        self.item_receivers.sprites.append(self.fighter.owner.entity_sprite.sprite)
        self.display_hovered = equipment_hover_text(
            self.currently_hovered, Vec2(self.width * 0.5, 100)
        )

    def currently_hovered(self) -> EquippableItem | None:
        item = None
        if draggable := self.draggable_collection.hand:
            item = draggable.item

        if draggable := self.draggable_collection.draggable_at_position(
            Vec2(*self.mouse)
        ):
            item = draggable.item

        return item

    def get_position(self) -> Vec2:
        return Vec2(self.left, self.bottom)

    def get_height(self) -> int:
        return self.height

    def _register_receivers(self):
        slot_x, slot_y = self.window.width * 0.9, 650
        for slot in ("_weapon", "_helmet", "_body"):
            receiver = ItemReceiver(
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
            )

            self.item_receivers.register(slot=slot, receiver=receiver),

            slot_y -= 150

        for receiver in self.inventory_grid.build_receivers():
            self.item_receivers.register_armory(receiver)

    def on_draw(self):
        self.grid_backing.draw_sized(position=(0, 202), size=(450, self.height - 4))
        self.item_receivers.sprites.draw(pixelated=True)
        self.draggable_collection.sprites.draw(pixelated=True)
        self.display_hovered.draw()

    def on_update(self, dt: float):
        self.display_hovered.on_update(...)

        if held := self.draggable_collection.hand:
            held.sprite.position = self.mouse

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.mouse = x, y
        self.lmb_pressed = button == arcade.MOUSE_BUTTON_LEFT
        if self.lmb_pressed:
            self.original_draggable_position = (
                self.draggable_collection.pick_up_at_mouse(self.mouse)
            )

    def _get_receiver_sprite(self, x: int, y: int) -> arcade.Sprite | None:
        """
        This currently requires an exact overlap of mouse position and ItemReceiver sprite
        """
        pos = (x, y)
        for sprite in self.item_receivers.sprites:
            if sprite.position == pos:
                return sprite

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if not self.draggable_collection.hand:
            return

        held = self.draggable_collection.hand

        self.mouse = x, y
        if self.lmb_pressed and button == arcade.MOUSE_BUTTON_LEFT:
            self.lmb_pressed = False

            item_slot_sprite, distance = arcade.get_closest_sprite(
                held.sprite, self.item_receivers.sprites
            )

            successfully_placed = False
            if arcade.check_for_collision(held.sprite, item_slot_sprite):
                successfully_placed = self.item_receivers.put_into_slot_at_sprite(
                    item_slot_sprite, held
                )

            if not successfully_placed:
                held.sprite.position = self.original_draggable_position

            self.draggable_collection.drop()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse = x, y

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.P:
            breakpoint()

    def on_resize(self, width, height):
        self.height = height - self.bottom
        self.inventory_grid.on_resize()
        for _, receiver in self.item_receivers._item_receivers.items():
            receiver.on_resize()
        self.display_hovered.x = self.window.width / 2
