import arcade

from src.gui.gui_utils import ScrollWindow, gen_heights
from src.gui.window_data import WindowData


# This should probably be broken up a little.
# Handles drawing the panel outlines and populating with calls to populate_x_pane
def draw_panels(
    margin: int,
    col_select: int,
    height: int,
    width: int,
    row_height: int,
    roster_scroll_window: ScrollWindow,
    team_scroll_window: ScrollWindow,
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
                center_y=height * 0.65,
                width=width * 0.485,
                height=height * 0.69,
                color=(218, 165, 32, 255),
            )

            if col == 0:
                instruction_text = "Up / Down arrows to change selection. Enter to move mercenaries between Roster and Team."

            else:
                instruction_text = "Up / Down arrows to change selection. Enter to move mercenaries between Team and Roster."

            arcade.Text(
                instruction_text,
                start_x=(x / 2),
                start_y=height * 0.35,
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
                    roster_scroll_window=roster_scroll_window,
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

# REFACTOR IN PROGRESS. BEHAVIOR NOW IMPLEMENTED IN RecruitmentPaneSection
# def draw_recruiting_panel(margin: int, height: int, recruitment_scroll_window, row_height):
#     arcade.draw_rectangle_outline(
#         center_x=(WindowData.width / 2) - 0.5,
#         center_y=height * 0.65,
#         width=WindowData.width *0.988,
#         height=height * 0.69,
#         color=(218, 165, 32, 255),
#     )

#     arcade.Text(
#         "Mercenaries for Hire!",
#         start_x=WindowData.width / 2,
#         start_y=height - margin * 8,
#         font_name=WindowData.font,
#         font_size=25,
#         anchor_x="center",
#     ).draw()

#     populate_recruitment_pane(recruitment_scroll_window, height, row_height)

# def populate_recruitment_pane(recruitment_scroll_window, height, row_height):
#     if recruitment_scroll_window.visible_items[1] is not None:
#         height = gen_heights(row_height=row_height + 6, y=height, spacing=3)
#         for merc, y2 in zip(range(recruitment_scroll_window.visible_size), height):

#             if merc == recruitment_scroll_window.visible_items[1]:
#                 # Colour the selected merc Gold
#                 color = (218, 165, 32, 255)
#                 mark1 = ">>> "
#                 mark2 = " $"
#             else:
#                 # otherwise colour white.
#                 color = arcade.color.WHITE
#                 mark1 = ""
#                 mark2 = ""
#             cost = f"{recruitment_scroll_window.visible_items[0][merc].cost} gp"
#             arcade.Text(
#                 f"{mark1} {recruitment_scroll_window.visible_items[0][merc].name.first_name.capitalize()} : {cost}",
#                 start_x=WindowData.width / 2,
#                 start_y=y2,
#                 font_name=WindowData.font,
#                 font_size=18,
#                 anchor_x="center",
#                 color=color,
#             ).draw()

def populate_roster_pane(x, col, row_height, margin, height, roster_scroll_window):
    """
    Print the name of each entity in a guild roster in a centralised column.
    We pass x through from the calling scope to center text relative to the column width.
    """
    if roster_scroll_window.visible_items[1] is not None:
        height = gen_heights(row_height=row_height, y=height, spacing=5)
        for merc, y2 in zip(range(roster_scroll_window.visible_size), height):

            if col == 0 and merc == roster_scroll_window.visible_items[1]:
                # Colour the selected merc Gold
                color = (218, 165, 32, 255)
                mark = " >>>"
            else:
                # otherwise colour white.
                color = arcade.color.WHITE
                mark = ""

            merc_index_in_items_array = roster_scroll_window.items.index(
                roster_scroll_window.visible_items[0][merc]
            )

            arcade.Text(
                f"{merc_index_in_items_array} {roster_scroll_window.visible_items[0][merc].name.first_name.capitalize()} {mark}",
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
        height = gen_heights(row_height=row_height, y=height, spacing=5)
        for merc, y2 in zip(range(team_scroll_window.visible_size), height):
            if col == 1 and merc == team_scroll_window.visible_items[1]:
                # Colour the selected merc Gold
                color = (218, 165, 32, 255)
                mark = "<<< "
            else:
                # otherwise colour white.
                color = arcade.color.WHITE
                mark = ""

            arcade.Text(
                f"{mark} {team_scroll_window.visible_items[0][merc].name.first_name.capitalize()} {merc}",
                start_x=(x / 2) - margin * 2,
                start_y=y2,
                font_name=WindowData.font,
                font_size=12,
                anchor_x="center",
                color=color,
            ).draw()
