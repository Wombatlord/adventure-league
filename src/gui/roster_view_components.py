import arcade
from src.gui.window_data import WindowData
from src.gui.gui_utils import gen_heights, ScrollWindow
from src.engine.engine import eng


def bottom_bar():
    margin = 5
    bar_height = 40
    arcade.draw_lrtb_rectangle_outline(
        left=margin * 2,
        right=WindowData.width - margin * 2,
        top=bar_height,
        bottom=margin,
        color=arcade.color.GOLDENROD,
    )

# This should probably be broken up a little.
# Handles drawing the panel outlines and populating with calls to populate_x_pane
def draw_panels(
    margin: int,
    col_select: int,
    height: int,
    width: int,
    row_height: int,
    roster_scroll_window: ScrollWindow,
    team_scroll_window: ScrollWindow
):
    for col in range(2):
        """
        Derive a value for x positions based on the total width including margins,
        Multiply by the value of col to shift the position by a column width right,
        Add margin & window width for col * 0
        Divide this by 2 to get the halfway point with respect to width + margins
        """
        x = (margin + width) * col + (margin + width) // 2

        """
            center_x: x / 2 positions center_x of the column at 1/4 of above x. ie, one column will fill half the vertical view.
            center_y: position center_y point slightly above halfway to leave space at the bottom.
            width: half the total window width with some adjustment by margin amounts.
            height: column is the full height of the window minus some adjustment by margin amounts.
            """
        if col_select.pos == col:
            # Highlight the selected column and write instructions at the bottom.
            arcade.draw_rectangle_outline(
                center_x=x / 2 - margin / 2,
                center_y=height * 0.5 + margin * 4,
                width=width * 0.5 - margin * 4,
                height=height - margin * 10,
                color=(218, 165, 32, 255),
            )

            if col == 0:
                instruction_text = "Up / Down arrows to change selection. Enter to move mercenaries between Roster and Team."

            else:
                instruction_text = "Up / Down arrows to change selection. Enter to move mercenaries between Team and Roster."

            arcade.Text(
                instruction_text,
                start_x=(x / 2),
                start_y=80,
                font_name=WindowData.font,
                font_size=10,
                anchor_x="center",
                multiline=True,
                width=350,
            ).draw()

        match col:
            case 0:
                # Roster Panel
                arcade.Text(
                    "Roster",
                    start_x=(x / 2) - margin * 2,
                    start_y=height - margin * 8,
                    font_name=WindowData.font,
                    font_size=25,
                    anchor_x="center",
                ).draw()

                arcade.Text(
                    "These are members of your guild, assign some to the team to send them on a mission.",
                    start_x=(x / 2) - margin * 2,
                    start_y=height - margin * 16,
                    font_name=WindowData.font,
                    font_size=10,
                    anchor_x="center",
                    multiline=True,
                    width=350,
                ).draw()

                populate_roster_pane(
                    x=x,
                    col=col_select.pos,
                    row_height=row_height,
                    margin=margin,
                    height=height,
                    roster_scroll_window=roster_scroll_window
                )

            case 1:
                # Team Panel
                arcade.Text(
                    "Team",
                    start_x=(x / 2) - margin * 2,
                    start_y=height - margin * 8,
                    font_name=WindowData.font,
                    font_size=25,
                    anchor_x="center",
                ).draw()

                arcade.Text(
                    "Mercenaries listed here will attempt the next mission!",
                    start_x=(x / 2) - margin * 2,
                    start_y=height - margin * 16,
                    font_name=WindowData.font,
                    font_size=10,
                    anchor_x="center",
                    multiline=True,
                    width=350,
                ).draw()

                populate_team_pane(
                    x=x,
                    col=col_select.pos,
                    row_height=row_height,
                    margin=margin,
                    height=height,
                    team_scroll_window=team_scroll_window,
                )


def populate_roster_pane(
    x, col, row_height, margin, height, roster_scroll_window
):
    """
    Print the name of each entity in a guild roster in a centralised column.
    We pass x through from the calling scope to center text relative to the column width.
    """

    height = gen_heights(row_height=row_height, height=height, spacing=5)
    for merc in range(roster_scroll_window.visible_size):
        y2 = next(height)

        if col == 0 and merc == roster_scroll_window.visible_items[1]:
        # Colour the selected merc Gold
            color = (218, 165, 32, 255)
        else:
        # otherwise colour white.
            color = arcade.color.WHITE
        
        arcade.Text(
            f"{roster_scroll_window.visible_items[0][merc].name.first_name.capitalize()} {merc}",
            start_x=(x / 2) - margin * 2,
            start_y=y2,
            font_name=WindowData.font,
            font_size=12,
            anchor_x="center",
            color=color,
        ).draw()


def populate_team_pane(x, col, row_height, margin, height, team_scroll_window):
    """
    Print the name of each entity assigned to the team in a centralised column.
    We pass x through from the calling scope to center text relative to the column width.
    """
    if team_scroll_window.visible_items[1] is not None:
        height = gen_heights(row_height=row_height, height=height, spacing=5)
        for merc in range(team_scroll_window.visible_size):
            y2 = next(height)

            if col == 1 and merc == team_scroll_window.visible_items[1]:
            # Colour the selected merc Gold
                color = (218, 165, 32, 255)
            else:
            # otherwise colour white.
                color = arcade.color.WHITE
            arcade.Text(
                f"{team_scroll_window.visible_items[0][merc].name.first_name.capitalize()} {merc}",
                start_x=(x / 2) - margin * 2,
                start_y=y2,
                font_name=WindowData.font,
                font_size=12,
                anchor_x="center",
                color=color,
            ).draw()
