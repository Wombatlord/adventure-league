from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

import arcade
from arcade.gui.widgets.text import UILabel

from src.engine.armory import Armory
from src.entities.combat.fighter import Fighter
from src.entities.gear.equippable_item import EquippableItem
from src.gui.components.buttons import nav_button
from src.gui.components.draggables import DraggableCollection
from src.gui.components.receivers import InventoryGrid, ItemReceiver, ReceiverCollection
from src.gui.generic_sections.command_bar import CommandBarSection
from src.gui.guild.inventory_grid import GridLoc, SnapGrid

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
            6,
            8,
            Vec2(60, 60),
            self.armory,
            self.gear,
            bottom_left=Vec2(0,215),
            original_draggable_position=self.get_original_draggable_pos,
        )
        self._register_receivers()

        self.draggable_collection = DraggableCollection(self.gear, self.inventory_grid)

        self.mouse = 0, 0
        self.lmb_pressed = False

        self.draggable = None
        self.original_draggable_position = None

    def get_original_draggable_pos(self):
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
