from __future__ import annotations
import arcade
from typing import Callable, TYPE_CHECKING
from src.entities.entity import Entity
from src.entities.gear.gear import Gear
from src.entities.sprites import EntitySprite
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
        self._filled_positions = 0

    @property
    def filled_positions(self):
        return self._filled_positions

    def item_stored(self):
        self._filled_positions += 1

    def item_removed(self):
        self._filled_positions -= 1


class GearSlots:
    def __init__(self, to_be_equipped: Gear) -> None:
        self.weapon_slot = arcade.SpriteSolidColor(
            50, 50, color=arcade.csscolor.AQUAMARINE
        )
        self.helmet_slot = arcade.SpriteSolidColor(50, 50, color=arcade.csscolor.VIOLET)
        self.body_slot = arcade.SpriteSolidColor(50, 50, color=arcade.csscolor.ORCHID)
        self.weapon_slot.position = 900, 550
        self.helmet_slot.position = 900, 400
        self.body_slot.position = 900, 250
        self.slot_sprite_list = arcade.SpriteList()
        self.slot_sprite_list.extend(
            [self.body_slot, self.helmet_slot, self.weapon_slot]
        )

        self.currently_equipped = to_be_equipped
        icons = [
            (item._sprite.sprite, label)
            for item, label in self.initial_equips(to_be_equipped)
        ]
        self.assign_initial_equip_icons_to_slots(icons)

        self.equip_list = arcade.SpriteList()

        for icon in icons:
            self.equip_list.append(icon[0])

    def initial_equips(self, equips):
        equipped = []
        for slot in equips._equippable_slots:
            match slot:
                case "_weapon":
                    if equips.weapon:
                        equipped.append((equips.weapon, "weapon"))
                case "_helmet":
                    if equips.helmet:
                        equipped.append((equips.helmet, "helmet"))
                case "_body":
                    if equips.body:
                        equipped.append((equips.body, "body"))

        return equipped

    def assign_initial_equip_icons_to_slots(self, icons: list):
        for icon_tuple in icons:
            match icon_tuple[1]:
                case "weapon":
                    icon_tuple[0].position = self.weapon_slot.position
                case "helmet":
                    icon_tuple[0].position = self.helmet_slot.position
                case "body":
                    icon_tuple[0].position = self.body_slot.position


class EquipSection(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        to_be_equipped: Entity,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)
        self.storage_zone = StorageZone()
        self.gear_slots = GearSlots(to_be_equipped=to_be_equipped.fighter.gear)

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
        equips: arcade.SpriteList = arcade.get_sprites_at_point((x, y), self.equip_list)

        # Have we clicked on an item? Otherwise do nothing.
        if len(equips) > 0:
            self.held_item: EntitySprite = equips[0]
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
                self.storage_zone.item_stored()
                padding = 35
                center_x = slot.center_x - slot.center_x + padding
                center_y = slot.center_y + slot.center_y // 2
                self.held_item.position = (
                    center_x * self.storage_zone.filled_positions,
                    center_y,
                )
                print(self.held_item.owner.owner.slot)
            else:
                self.held_item.position = slot.center_x, slot.center_y
                self.storage_zone.item_removed()
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
        self, to_be_equipped: Entity, parent_factory: Callable[[], arcade.View]
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
                    text=self.to_be_equipped.name.name_and_title,
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
            to_be_equipped=self.to_be_equipped,
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
