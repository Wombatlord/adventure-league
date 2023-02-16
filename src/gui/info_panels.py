from typing import Callable

import arcade
from arcade.gui import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton

from src.engine.init_engine import eng
from src.gui.states import ViewStates
from src.gui.ui_styles import ADVENTURE_STYLE
from src.gui.window_data import WindowData


# This module provides functions for populating the information bar in a particular view
def style_command_bar(buttons: list[UIFlatButton]) -> list[UIFlatButton]:
    """style_command_bar expects to be passed a list of buttons that will occupy
    the command bar UI component. It applies consistent styling and spacing to the buttons
    in place so that they have responsive scaling.
    
    Args:
        buttons (list[UIFlatButton]): the list of buttons to be styled.

    Returns:
        list[UIFlatButton]: the styled (in place) buttons.
    """    
    if not buttons:
        return []

    for button in buttons:
        button.size_hint=(1/len(buttons), 1)
        button.style=ADVENTURE_STYLE
        button.with_border(width=2, color=arcade.color.GOLDENROD)

    return buttons

def populate_guild_view_info_panel():
    margin = 5
    arcade.draw_lrtb_rectangle_outline(
        left=margin,
        right=WindowData.width - margin,
        top=WindowData.height * 0.3,
        bottom=margin * 6,
        color=arcade.color.GOLDENROD,
    )
    
    arcade.Text(
            f"{eng.game_state.guild.name}",
            WindowData.width / 2,
            WindowData.height * 0.3 - 25,
            anchor_x="center",
            color=arcade.color.GOLDENROD,
            font_name=WindowData.font,
        ).draw()

def populate_roster_view_info_panel(merc, viewstate):
    """RosterView can switch between showing Roster or Recruitment information depending on the passed viewstate.
    Checking which viewstate is currently being passed allows for changing the particular text rendered without bespoke functions for each.

    Args:
        merc (Entity): An entity which can be recruited / assigned between roster and team.
        viewstate (Enum): Indicates the state of the View (roster info or recruitment info)
    """
    margin = 5
    arcade.draw_lrtb_rectangle_outline(
        left=margin,
        right=WindowData.width - margin,
        top=WindowData.height * 0.3,
        bottom=margin * 6,
        color=arcade.color.GOLDENROD,
    )
    
    if viewstate == ViewStates.ROSTER:
        text = "Assign members to the team before embarking on a mission!"
    
    if viewstate == ViewStates.RECRUIT:
        text = f"Press Enter to recruit a Mercenary to the {eng.game_state.guild.name}"
    
    if merc is not None:
        stat_bar = f"LVL: {merc.fighter.level}  |  HP: {merc.fighter.hp}  |  ATK: {merc.fighter.power}  |  DEF: {merc.fighter.defence}"
        arcade.Text(
            stat_bar,
            start_x=(WindowData.width / 2),
            start_y=WindowData.height * 0.15,
            font_name=WindowData.font,
            font_size=20,
            anchor_x="center",
        ).draw()
    
    arcade.Text(
            text,
            start_x=(WindowData.width / 2),
            start_y=WindowData.height * 0.25,
            font_name=WindowData.font,
            font_size=18,
            anchor_x="center",
        ).draw()

def populate_mission_view_info_panel():
    margin = 5
    arcade.draw_lrtb_rectangle_outline(
        left=margin,
        right=WindowData.width - margin,
        top=WindowData.height * 0.3,
        bottom=margin * 6,
        color=arcade.color.GOLDENROD,
    )
    
    arcade.Text(
            f"Press Enter to embark on a mission!",
            WindowData.width / 2,
            WindowData.height * 0.3 - 25,
            anchor_x="center",
            color=arcade.color.GOLDENROD,
            font_size=18,
            font_name=WindowData.font,
        ).draw()
    
    if len(eng.game_state.team.members) == 0:
        arcade.Text(
                f"No guild members are assigned to the team!",
                start_x=WindowData.width / 2,
                start_y=WindowData.height * 0.3 - 75,
                anchor_x="center",
                color=arcade.color.RED_DEVIL,
                font_size=18,
                font_name=WindowData.font,
            ).draw()
    
    else:
        arcade.Text(
                f"{len(eng.game_state.team.members)} guild members are ready for battle!",
                start_x=WindowData.width / 2,
                start_y=WindowData.height * 0.3 - 75,
                anchor_x="center",
                color=arcade.color.GOLDENROD,
                font_size=16,
                font_name=WindowData.font,
            ).draw()