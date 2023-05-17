from __future__ import annotations
import arcade
from typing import Callable, TYPE_CHECKING
from src.gui.components.buttons import nav_button
from src.gui.generic_sections.command_bar import CommandBarSection
from arcade.gui.widgets.text import UILabel
from src.engine.init_engine import eng

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.gui.window_data import WindowData
from src.gui.generic_sections.info_pane import InfoPaneSection


class StorageZone:
    def __init__(self) -> None:
        self.zone = arcade.SpriteSolidColor(
            500, 520, 250, 460, color=arcade.csscolor.GRAY
        )
        self.unequipped_count = 0


class GearSlots:
    def __init__(self) -> None:
        self.weapon_slot = arcade.SpriteSolidColor(
            50, 50, color=arcade.csscolor.AQUAMARINE
        )
        self.helmet_slot = arcade.SpriteSolidColor(50, 50, color=arcade.csscolor.VIOLET)
        self.body_slot = arcade.SpriteSolidColor(50, 50, color=arcade.csscolor.ORCHID)
        self.helmet_slot.position = 900, 250
        self.weapon_slot.position = 900, 400
        self.body_slot.position = 900, 550

        self.currently_equipped = eng.game_state.guild.roster[0].fighter.gear

        self.equipped_icons = [
            self.currently_equipped.weapon._sprite.sprite,
            self.currently_equipped.helmet._sprite.sprite,
            self.currently_equipped.body._sprite.sprite,
        ]

        self.currently_equipped.weapon._sprite.sprite.position = (
            self.weapon_slot.position
        )
        self.currently_equipped.helmet._sprite.sprite.position = (
            self.helmet_slot.position
        )
        self.currently_equipped.body._sprite.sprite.position = self.body_slot.position

        self.slot_sprite_list = arcade.SpriteList()
        self.slot_sprite_list.extend(
            [self.weapon_slot, self.helmet_slot, self.body_slot]
        )
        self.equip_list = arcade.SpriteList()
        self.equip_list.extend(self.equipped_icons)


class EquipSection(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)
        self.storage_zone = StorageZone()
        self.gear_slots = GearSlots()

        self.held_item = None
        self.held_item_original_position = None

        self.slot_list: arcade.SpriteList = arcade.SpriteList()

        self.slot_list.extend(
            [self.storage_zone.zone, *self.gear_slots.slot_sprite_list]
        )

        self.equip_list = arcade.SpriteList()
        self.equip_list.extend([*self.gear_slots.equip_list])

    def on_draw(self):
        self.slot_list.draw()
        self.equip_list.draw(pixelated=True)

    def pull_to_top(self, card: arcade.Sprite):
        """Pull draggable to top of rendering order (last to render, looks on-top)"""
        self.equip_list.remove(card)
        self.equip_list.append(card)

    def on_mouse_press(self, x, y, button, key_modifiers):
        # Get sprite at the mouse cursor
        equips = arcade.get_sprites_at_point((x, y), self.equip_list)

        # Have we clicked on an item? Otherwise do nothing.
        if len(equips) > 0:
            self.held_item = equips[0]
            self.held_item_original_position = self.held_item.position
            # Put on top in drawing order
            self.pull_to_top(self.held_item)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        # If we don't have an item, who cares
        if not self.held_item:
            return

        # Find the closest slot / zone, in case we are in contact with more than one
        slot, distance = arcade.get_closest_sprite(self.held_item, self.slot_list)
        reset_position = True

        # See if we are in contact with the closest slot / zone
        if arcade.check_for_collision(self.held_item, slot):
            # For each held sprite, move it to the slot / zone we dropped on

            # Move sprite to proper position
            if slot == self.storage_zone.zone:
                self.storage_zone.unequipped_count += 1
                padding = 35
                center_x = slot.center_x - slot.center_x + padding
                center_y = slot.center_y + slot.center_y // 2
                self.held_item.position = (
                    center_x * self.storage_zone.unequipped_count,
                    center_y,
                )

            else:
                self.held_item.position = slot.center_x, slot.center_y
                self.storage_zone.unequipped_count -= 1
            # Success, don't reset position of sprite
            reset_position = False

        # Released on valid zone?
        if reset_position:
            # Where-ever we were dropped, it wasn't valid. Reset the sprite's position
            # to its original spot.
            self.held_item.position = self.held_item_original_position

        # We are no longer holding an item
        self.held_item = None

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        if self.held_item:
            self.held_item.center_x = x
            self.held_item.center_y = y


class EquipView(arcade.View):
    """Draw a view displaying information about a guild"""

    def __init__(
        self, fighter_to_equip: Fighter, parent_factory: Callable[[], arcade.View]
    ):
        super().__init__()
        self.parent_factory = parent_factory

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
                    text="placeholder text", font_size=24, font_name=WindowData.font
                )
            ],
        )

        # CommandBar config
        self.buttons = [
            nav_button(self.parent_factory, "Guild"),
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
