import arcade
from typing import Optional
from arcade import Color
from arcade.text import FontNameOrNames
from dataclasses import dataclass
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.events import UIEvent
from arcade.gui.style import UIStyleBase
from src.gui.window_data import WindowData
from src.engine.init_engine import eng
from src.gui.states import ViewStates

# This module provides functions for populating the information bar in a particular view
def command_bar(viewstate: ViewStates):
    margin = 5
    match viewstate:
        case ViewStates.GUILD:
            commands = ["[m]issions", "[r]oster", "[n]ew missions"]
            width=WindowData.width * 0.3
        
        case ViewStates.ROSTER:
            commands = ["[r]ecruit", "[g]uild"]
            width=WindowData.width * 0.48
            
        case ViewStates.RECRUIT:
            commands = ["[r]oster", "[g]uild"]
            width=WindowData.width * 0.48
            
        case ViewStates.MISSIONS:
            commands = ["[g]uild"]
            width = WindowData.width * 0.98
    
    # View navigation command bar
    for col in range(len(commands)):
        x = (margin + WindowData.width) * col + margin + WindowData.width // 2
        arcade.draw_rectangle_outline(
            center_x=x / len(commands) - margin,
            center_y=margin * 3,
            width=width,
            height=margin * 4,
            color=arcade.color.GOLDENROD,
        )

        arcade.Text(
            text=commands[col],
            start_x=(x / len(commands)),
            start_y=margin * 2,
            anchor_x="center",
            font_name=WindowData.font,
        ).draw()

@dataclass
class UIStyle(UIStyleBase):
    font_size: int = 12
    font_name: FontNameOrNames = WindowData.font
    font_color: Color = arcade.color.WHITE
    bg: Color = arcade.color.BLACK
    border: Optional[Color] = None
    border_width: int = 0

ADVENTURE_STYLE = {
        "normal": UIStyle(),
        "hover": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.GOLD,
            bg=(21, 19, 21),
            border=None,
            border_width=0,
        ),
        "press": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.BLACK,
            bg=arcade.color.WHITE,
            border=None,
            border_width=0,
        ),
        "disabled": UIStyle(
            font_size=12,
            font_name=WindowData.font,
            font_color=arcade.color.WHITE,
            bg=arcade.color.GRAY,
            border=None,
            border_width=0,
        )
    }

def command_bar_GUI(viewstate: ViewStates, handler):
    buttons = []
    match viewstate:
        case ViewStates.GUILD:
            commands = ["Missions", "Roster", "New Missions"]
        
        case ViewStates.ROSTER:
            commands = ["Recruit ", "Guild"]
            
        case ViewStates.RECRUIT:
            commands = ["Roster", "Guild"]
            
        case ViewStates.MISSIONS:
            commands = ["Guild"]
    
    # View navigation command bar
    for command in commands:
        buttons.append(UIFlatButton(text=f"{command}", size_hint=(1/len(commands), 1), style=ADVENTURE_STYLE))
    
    for button in buttons:
            button.with_border(width=2, color=arcade.color.GOLDENROD)
            button.on_click = handler
    
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