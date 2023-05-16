from __future__ import annotations
import arcade
from typing import Callable, TYPE_CHECKING
from src.gui.components.buttons import nav_button
from src.gui.generic_sections.command_bar import CommandBarSection
from arcade.gui.widgets.text import UILabel

if TYPE_CHECKING:
    from src.entities.combat.fighter import Fighter

from src.gui.window_data import WindowData
from src.gui.generic_sections.info_pane import InfoPaneSection

CARD_VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_SUITS = ["Clubs", "Hearts", "Spades", "Diamonds"]


class Card(arcade.Sprite):
    """Card sprite"""

    def __init__(self, suit, value, scale=1):
        """Card constructor"""

        # Attributes for suit and value
        self.suit = suit
        self.value = value

        # Image to use for the sprite when face up
        self.image_file_name = (
            f":resources:images/cards/card{self.suit}{self.value}.png"
        )

        # Call the parent
        super().__init__(
            self.image_file_name,
            scale,
            hit_box_algorithm="None",
            center_x=100,
            center_y=400,
        )


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

        self.fighter_to_equip = Card("Spades", "A")

        self.held_item = None
        self.held_item_original_position = None
        self.equip_list = arcade.SpriteList()
        self.equip_list.append(self.fighter_to_equip)
        
        self.slot_list: arcade.SpriteList = arcade.SpriteList()

        # Create the mats for the bottom face down and face up piles
        equippable_slot = arcade.SpriteSolidColor(150, 250, color=arcade.csscolor.AQUAMARINE)
        original_slot = arcade.SpriteSolidColor(150, 250, color=arcade.csscolor.VIOLET)
        third_slot = arcade.SpriteSolidColor(150, 250, color=arcade.csscolor.ORCHID)
        original_slot.position = 100, 400
        equippable_slot.position = 500, 400
        third_slot.position = 900, 400
        self.slot_list.extend([equippable_slot, original_slot, third_slot])
        
    def on_draw(self):
        self.slot_list.draw()
        self.equip_list.draw()

    def pull_to_top(self, card: arcade.Sprite):
        """Pull card to top of rendering order (last to render, looks on-top)"""

        # Remove, and append to the end
        self.equip_list.remove(card)
        self.equip_list.append(card)

    def on_mouse_press(self, x, y, button, key_modifiers):
        """Called when the user presses a mouse button."""

        # Get list of cards we've clicked on
        equips = arcade.get_sprites_at_point((x, y), self.equip_list)

        # Have we clicked on a card?
        if len(equips) > 0:
            # All other cases, grab the face-up card we are clicking on
            self.held_item = equips[0]
            # Save the position
            self.held_item_original_position = self.held_item.position
            # Put on top in drawing order
            self.pull_to_top(self.held_item)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        # If we don't have an item, who cares
        if not self.held_item:
            return
        
        # Find the closest pile, in case we are in contact with more than one
        slot, distance = arcade.get_closest_sprite(self.held_item, self.slot_list)
        reset_position = True

        # See if we are in contact with the closest pile
        if arcade.check_for_collision(self.held_item, slot):

            # For each held card, move it to the pile we dropped on

            # Move cards to proper position
            self.held_item.position = slot.center_x, slot.center_y

            # Success, don't reset position of cards
            reset_position = False

            # Release on top play pile? And only one card held?
        if reset_position:
            # Where-ever we were dropped, it wasn't valid. Reset the each card's position
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
            texts=[UILabel(text="placeholder text",font_size=24, font_name=WindowData.font)],
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
