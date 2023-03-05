import arcade
from arcade.gui import UIManager
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.widgets.text import UILabel

from src.engine.init_engine import eng
from src.gui.buttons import CommandBarMixin
from src.gui.gui_components import (
    box_containing_horizontal_label_pair,
    create_colored_UILabel_header,
    entity_labels_names_only,
    entity_labels_with_cost,
    horizontal_box_pair,
    single_box,
    vertical_box_pair,
    vstack_of_three_boxes,
)
from src.gui.gui_utils import Cycle, ScrollWindow
from src.gui.states import MissionCards
from src.gui.ui_styles import ADVENTURE_STYLE
from src.gui.window_data import WindowData


class CommandBarSection(arcade.Section, CommandBarMixin):
    manager: UIManager
    anchor: UIAnchorLayout
    command_box: UIBoxLayout
    buttons: list[UIFlatButton]

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        buttons: list[UIFlatButton],
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.manager = UIManager()
        self.buttons = buttons

        self.manager.add(
            single_box(
                self.bottom,
                self.height,
                self.command_bar,
                vertical=False,
                border_width=0,
            )
        )

    @property
    def command_bar(self) -> list[UIFlatButton]:
        return self.style_command_bar(buttons=self.buttons)

    def flush(self):
        self.manager = UIManager()

        self.manager.add(
            single_box(
                self.bottom,
                self.height,
                self.command_bar,
                vertical=False,
                border_width=0,
            )
        )

    def on_draw(self) -> None:
        self.manager.draw()

    def style_command_bar(self, buttons: list[UIFlatButton]) -> list[UIFlatButton]:
        """
        style_command_bar expects to be passed a list of buttons that will occupy
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
            button.size_hint = (1 / len(buttons), 1)
            button.style = ADVENTURE_STYLE
            button.with_border(width=3, color=arcade.color.GOLD)

        return buttons


class InfoPaneSection(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        margin: int,
        texts: list[UILabel],
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.manager = UIManager()
        self.margin = margin
        self.texts = texts

        self.manager.add(
            single_box(self.bottom, self.height, self.texts, (10, 0, 0, 0))
        )

    def flush(self):
        self.manager = UIManager()

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.width = width


def _highlight_selection(
    scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]
) -> None:
    """
    Highlight the currently selected entry in the recruitment pane with a color and ">>" selection mark prepended to the text

    Args:
        scroll_window (ScrollWindow): ScrollWindow contains both the selection tracking via ScrollWindow.position.pos,
                                      and an array of the entities which are represented in the UILabels.

        labels (tuple[UIWidget]): The UILabels which are actually drawn in the UI by the UIManager.
                                  Use ScrollWindow.items fields to recreate the non-selected label text.
                                  May be empty if for example all roster members are assigned to team or vice versa.
    """
    if len(labels) > 0:
        entity_labels = labels

        # Set all entity_label colors to white and text to non-selected string.
        for entity_label in entity_labels:
            entity_label.label.color = arcade.color.WHITE
            entity_label.label.text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}: {scroll_window.items[entity_labels.index(entity_label)].cost} gp"

        # Set selected entity_label color to gold and text to selection string
        entity_labels[scroll_window.position.pos].label.color = arcade.color.GOLD
        entity_labels[
            scroll_window.position.pos
        ].label.text = f">> {entity_labels[scroll_window.position.pos].label.text}"


def _clear_highlight_selection(
    scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]
) -> None:
    """
    Highlight the currently selected entry in the recruitment pane with a color and ">>" selection mark prepended to the text

    Args:
        scroll_window (ScrollWindow): ScrollWindow contains both the selection tracking via ScrollWindow.position.pos,
                                      and an array of the entities which are represented in the UILabels.

        labels (tuple[UIWidget]): The UILabels which are actually drawn in the UI by the UIManager.
                                  Use ScrollWindow.items fields to recreate the non-selected label text.
    """
    entity_labels = labels

    # Set all entity_label colors to white and text to non-selected string.
    for entity_label in entity_labels:
        entity_label.label.color = arcade.color.WHITE
        entity_label.label.text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}: {scroll_window.items[entity_labels.index(entity_label)].cost} gp"


class RecruitmentPaneSection(arcade.Section):
    recruits_box_children: tuple[UIWidget]

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.manager = UIManager()
        self.recruitment_scroll_window = ScrollWindow(
            eng.game_state.entity_pool.pool, 10, 10
        )
        self.margin = 2
        self.recruits_labels: tuple[UIWidget] = entity_labels_with_cost(
            self.recruitment_scroll_window
        )
        self.header = create_colored_UILabel_header(
            "Mercenaries For Hire!", arcade.color.GO_GREEN, font_size=30, height=45
        )

        content = (*self.header, *self.recruits_labels)

        self.manager.add(
            single_box(
                self.bottom, self.height - self.bottom, content, padding=(50, 0, 0, 0)
            )
        )
        self.guild_funds_label = None

        _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)

    def flush(self):
        self.width = WindowData.width - 2
        self.height = WindowData.height - 2
        self.manager = UIManager()

        self.recruitment_scroll_window = ScrollWindow(
            eng.game_state.entity_pool.pool, 10, 10
        )

        self.recruits_labels: tuple[UIWidget] = entity_labels_with_cost(
            self.recruitment_scroll_window
        )

        content = (*self.header, *self.recruits_labels)

        self.manager.add(
            single_box(
                self.bottom, self.height - self.bottom, content, padding=(15, 0, 0, 0)
            )
        )

        self.guild_funds_label = (
            self.view.info_pane_section.manager.children[0][0]
            .children[0]
            .children[2]
            .children[1]
        )

        _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.manager.children[0][0].resize(
            width=width - self.margin, height=(height - self.bottom) - self.margin
        )

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.UP:
            """
            Decrement the recruitment_scroll_window.position.pos
            ie. move selection position up in the UI.
            """
            self.recruitment_scroll_window.decr_selection()
            _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)
            self.manager.trigger_render()

        if symbol == arcade.key.DOWN:
            """
            Increment the recruitment_scroll_window.position.pos
            ie. move selection position down in the UI.
            """
            self.recruitment_scroll_window.incr_selection()
            _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)
            self.manager.trigger_render()

        if symbol == arcade.key.ENTER:
            # If the total amount of guild members does not equal the roster_limit, recruit the selected mercenary to the guild.
            if (
                len(eng.game_state.guild.roster) + len(eng.game_state.team.members)
                < eng.game_state.guild.roster_limit
            ):
                eng.recruit_entity_to_guild(
                    eng.game_state.entity_pool.pool.index(
                        self.recruitment_scroll_window.selection
                    )
                )

                # Assign currently selected child to pass to the remove() func of the UIBoxLayout
                # to maintain correspondence with the recruitment_scroll_window.items
                highlighted_label = self.recruits_labels[
                    self.recruitment_scroll_window.position.pos
                ]

                # Remove the UILabel from UIBoxLayout and pop the corresponding item from the recruitment_scroll_window.
                self.manager.children[0][0].children[0].remove(highlighted_label)
                self.recruitment_scroll_window.pop()

                # Update state
                self.recruits_labels = (
                    self.manager.children[0][0].children[0].children[1:]
                )

                # Ensure highlighting carries over to the now selected recruit.
                _highlight_selection(
                    self.recruitment_scroll_window,
                    self.recruits_labels,
                )
                self.guild_funds_label.label.text = f"{eng.game_state.guild.funds} gp"

                self.manager.trigger_render()


def _highlight_roster_or_team_selection(
    scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]
) -> None:
    """
    Highlight the currently selected entry in the recruitment pane with a color and ">>" selection mark prepended to the text

    Args:
        scroll_window (ScrollWindow): ScrollWindow contains both the selection tracking via ScrollWindow.position.pos,
                                      and an array of the entities which are represented in the UILabels.

        labels (tuple[UIWidget]): The UILabels which are actually drawn in the UI by the UIManager.
                                  Use ScrollWindow.items fields to recreate the non-selected label text.
                                  May be empty if for example all roster members are assigned to team or vice versa.
    """
    if len(labels) > 0:
        entity_labels = labels

        # Set all entity_label colors to white and text to non-selected string.
        for entity_label in entity_labels:
            entity_label.label.color = arcade.color.WHITE
            entity_label.label.text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}"

        # Set selected entity_label color to gold and text to selection string
        entity_labels[scroll_window.position.pos].label.color = arcade.color.GOLD
        entity_labels[
            scroll_window.position.pos
        ].label.text = f">> {entity_labels[scroll_window.position.pos].label.text}"


def _clear_highlight_roster_or_team_selection(
    scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]
) -> None:
    """
    Highlight the currently selected entry in the recruitment pane with a color and ">>" selection mark prepended to the text

    Args:
        scroll_window (ScrollWindow): ScrollWindow contains both the selection tracking via ScrollWindow.position.pos,
                                      and an array of the entities which are represented in the UILabels.

        labels (tuple[UIWidget]): The UILabels which are actually drawn in the UI by the UIManager.
                                  Use ScrollWindow.items fields to recreate the non-selected label text.
    """
    entity_labels = labels

    # Set all entity_label colors to white and text to non-selected string.
    for entity_label in entity_labels:
        entity_label.label.color = arcade.color.WHITE
        entity_label.label.text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}"


class RosterAndTeamPaneSection(arcade.Section):
    roster_box_children: tuple[UIWidget]
    team_box_children: tuple[UIWidget]

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.manager = UIManager()
        self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
        self.team_scroll_window = ScrollWindow(
            eng.game_state.guild.team.members, 10, 10
        )

        # Indicates whether Roster or Team pane is the active pane.
        self.pane_selector = Cycle(2)
        self.pane_id = (0, 1)

        self.roster_header = create_colored_UILabel_header(
            "Roster", arcade.color.BYZANTIUM, font_size=30, height=45
        )
        self.team_header = create_colored_UILabel_header(
            "Team", arcade.color.BRASS, font_size=30, height=45
        )

        self.roster_labels: tuple[UIWidget] = entity_labels_names_only(
            self.roster_scroll_window
        )
        self.team_labels: tuple[UIWidget] = entity_labels_names_only(
            self.team_scroll_window
        )

        self.roster_content = (*self.roster_header, *self.roster_labels)
        self.team_content = (*self.team_header, *self.team_labels)
        self.manager.add(
            horizontal_box_pair(
                self.bottom,
                self.height - self.bottom,
                self.roster_content,
                self.team_content,
                padding=(10, 0, 0, 0),
            )
        )
        self._highlight_pane()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def flush(self):
        self.width = WindowData.width - 2
        self.height = WindowData.height - 2
        self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
        self.manager = UIManager()

        self.roster_labels: tuple[UIWidget] = entity_labels_names_only(
            self.roster_scroll_window
        )
        self.team_labels: tuple[UIWidget] = entity_labels_names_only(
            self.team_scroll_window
        )

        self.roster_content = (*self.roster_header, *self.roster_labels)
        self.team_content = (*self.team_header, *self.team_labels)

        self.manager.add(
            horizontal_box_pair(
                self.bottom,
                self.height - self.bottom,
                self.roster_content,
                self.team_content,
                padding=(10, 0, 0, 0),
            )
        )
        self.manager.enable()
        self._highlight_pane()

    def _highlight_pane(self):
        if self.pane_selector.pos == self.pane_id[0]:
            self.manager.children[0][0].children[0]._border_width = 5
            self.manager.children[0][0].children[1]._border_width = 0

            if len(self.team_labels) > 0:
                _clear_highlight_roster_or_team_selection(
                    self.team_scroll_window, self.team_labels
                )

            if len(self.roster_labels) > 0:
                _highlight_roster_or_team_selection(
                    self.roster_scroll_window, self.roster_labels
                )

        if self.pane_selector.pos == self.pane_id[1]:
            self.manager.children[0][0].children[0]._border_width = 0
            self.manager.children[0][0].children[1]._border_width = 5

            if len(self.roster_labels) > 0:
                _clear_highlight_roster_or_team_selection(
                    self.roster_scroll_window, self.roster_labels
                )

            if len(self.team_labels) > 0:
                _highlight_roster_or_team_selection(
                    self.team_scroll_window, self.team_labels
                )

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.manager.children[0][0].resize(width=width - 2, height=height - self.bottom)

    def on_key_press(self, symbol: int, modifiers: int):
        """
        Left / Right changes focus between Roster & Team panes:
        Up / Down to change label selection and apply highlighting
        Enter assigns the highlighted member to the team or the roster
        """
        match symbol:
            case arcade.key.LEFT:
                self.pane_selector.decr()
                self._highlight_pane()

            case arcade.key.RIGHT:
                self.pane_selector.incr()
                self._highlight_pane()

            case arcade.key.UP:
                if self.pane_selector.pos == self.pane_id[0]:
                    self.roster_scroll_window.decr_selection()
                    _highlight_roster_or_team_selection(
                        self.roster_scroll_window,
                        self.roster_labels,
                    )
                    self.manager.trigger_render()

                if self.pane_selector.pos == self.pane_id[1]:
                    self.team_scroll_window.decr_selection()
                    _highlight_roster_or_team_selection(
                        self.team_scroll_window,
                        self.team_labels,
                    )
                    self.manager.trigger_render()

            case arcade.key.DOWN:
                if self.pane_selector.pos == self.pane_id[0]:
                    self.roster_scroll_window.incr_selection()
                    _highlight_roster_or_team_selection(
                        self.roster_scroll_window,
                        self.roster_labels,
                    )
                    self.manager.trigger_render()

                if self.pane_selector.pos == self.pane_id[1]:
                    self.team_scroll_window.incr_selection()
                    _highlight_roster_or_team_selection(
                        self.team_scroll_window,
                        self.team_labels,
                    )
                    self.manager.trigger_render()

            case arcade.key.ENTER:
                if (
                    self.pane_selector.pos == self.pane_id[0]
                    and len(self.roster_scroll_window.items) > 0
                ):
                    # Move merc from ROSTER to TEAM. Increase Cycle.length for team, decrease Cycle.length for roster.
                    # Assign to Team & Remove from Roster.
                    self.team_scroll_window.append(self.roster_scroll_window.selection)
                    eng.game_state.guild.team.assign_to_team(
                        self.roster_scroll_window.selection
                    )
                    self.roster_scroll_window.pop()

                    # Update Engine state.
                    eng.game_state.guild.roster = self.roster_scroll_window.items
                    eng.game_state.guild.team.members = self.team_scroll_window.items

                    self.flush()

                if (
                    self.pane_selector.pos == self.pane_id[1]
                    and len(self.team_scroll_window.items) > 0
                ):
                    # Move merc from TEAM to ROSTER
                    self.roster_scroll_window.append(self.team_scroll_window.selection)

                    # Remove from Team array
                    self.team_scroll_window.pop()

                    # Update Engine state.
                    eng.game_state.guild.roster = self.roster_scroll_window.items
                    eng.game_state.guild.team.members = self.team_scroll_window.items

                    self.flush()


class MissionsSection(arcade.Section):
    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        missions,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.manager = UIManager()
        self.missions = missions
        self.mission_selection = Cycle(3, 0)

        headers = (
            create_colored_UILabel_header(
                header_string=self.missions[0].description, color=arcade.color.GOLD
            ),
            create_colored_UILabel_header(
                header_string=self.missions[1].description, color=arcade.color.GOLD
            ),
            create_colored_UILabel_header(
                header_string=self.missions[2].description, color=arcade.color.GOLD
            ),
        )

        labels = (
            (
                *headers[0],
                box_containing_horizontal_label_pair(
                    (
                        ("Boss:", "left", 16, arcade.color.GOLD),
                        (
                            self.missions[0].boss.name.name_and_title,
                            "left",
                            16,
                            arcade.color.ALABAMA_CRIMSON,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        25,
                    ),
                    space_between_labels=25,
                ),
                box_containing_horizontal_label_pair(
                    (
                        ("Rewards:", "left", 14, arcade.color.GOLD),
                        (
                            self.missions[0].peek_reward(),
                            "left",
                            16,
                            arcade.color.PALATINATE_BLUE,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        50,
                    ),
                    space_between_labels=25,
                ),
            ),
            (
                *headers[1],
                box_containing_horizontal_label_pair(
                    (
                        ("Boss:", "left", 16, arcade.color.GOLD),
                        (
                            self.missions[1].boss.name.name_and_title,
                            "left",
                            16,
                            arcade.color.ALABAMA_CRIMSON,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        25,
                    ),
                    space_between_labels=25,
                ),
                box_containing_horizontal_label_pair(
                    (
                        ("Rewards:", "left", 14, arcade.color.GOLD),
                        (
                            self.missions[1].peek_reward(),
                            "left",
                            16,
                            arcade.color.PALATINATE_BLUE,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        50,
                    ),
                    space_between_labels=25,
                ),
            ),
            (
                *headers[2],
                box_containing_horizontal_label_pair(
                    (
                        ("Boss:", "left", 16, arcade.color.GOLD),
                        (
                            self.missions[2].boss.name.name_and_title,
                            "left",
                            16,
                            arcade.color.ALABAMA_CRIMSON,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        25,
                    ),
                    space_between_labels=25,
                ),
                box_containing_horizontal_label_pair(
                    (
                        ("Rewards:", "left", 14, arcade.color.GOLD),
                        (
                            self.missions[2].peek_reward(),
                            "left",
                            16,
                            arcade.color.PALATINATE_BLUE,
                        ),
                    ),
                    padding=(
                        0,
                        0,
                        0,
                        50,
                    ),
                    space_between_labels=25,
                ),
            ),
        )

        self.manager.add(
            vstack_of_three_boxes(
                self.bottom,
                self.height,
                *labels,
            ),
        )

        self.manager.children[0][0].children[0]._border_width = 5
        self.manager.children[0][0].children[1]._border_width = 0
        self.manager.children[0][0].children[2]._border_width = 0

    def scroll_mission_selection(self):
        match self.mission_selection.pos:
            case MissionCards.TOP.value:
                self.manager.children[0][0].children[0]._border_width = 5
                self.manager.children[0][0].children[1]._border_width = 0
                self.manager.children[0][0].children[2]._border_width = 0

            case MissionCards.MIDDLE.value:
                self.manager.children[0][0].children[0]._border_width = 0
                self.manager.children[0][0].children[1]._border_width = 5
                self.manager.children[0][0].children[2]._border_width = 0

            case MissionCards.BOTTOM.value:
                self.manager.children[0][0].children[0]._border_width = 0
                self.manager.children[0][0].children[1]._border_width = 0
                self.manager.children[0][0].children[2]._border_width = 5

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.manager.children[0][0].resize(width=width - 2, height=height - self.bottom)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.UP:
                self.mission_selection.decr()
                self.scroll_mission_selection()
                print(self.missions[self.mission_selection.pos].description)

            case arcade.key.DOWN:
                self.mission_selection.incr()
                self.scroll_mission_selection()
                print(self.missions[self.mission_selection.pos].description)


class CombatGridSection(arcade.Section):
    TILE_BASE_DIMS = (256, 512)
    Y_OFFSET = WindowData.height
    SCALE_FACTOR = 0.2

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)
        self.encounter_room = None

        self.manager = UIManager()

        self.manager.add(
            single_box(
                bottom,
                height,
                children=[]
            ).with_border(width=2, color=arcade.color.BLUEBONNET),
        )
        
        self.tile_sprite_list = arcade.SpriteList()
        for x in range(9, -1, -1):
            for y in range(9, -1, -1):
                self.tile_sprite_list.append(self.tile_at(x,y))

        self.dudes_sprite_list = arcade.SpriteList()

    def grid_offset(self, x: int, y: int) -> tuple[int, int]:
        grid_scale = 0.75
        return (
            (-y + x)*grid_scale*self.TILE_BASE_DIMS[0]*self.SCALE_FACTOR*(0.7),
            (x + y)*grid_scale*self.TILE_BASE_DIMS[0]*self.SCALE_FACTOR*(1/3),
        )
         
    def tile_at(self, x: int, y: int) -> arcade.Sprite:
        tile = arcade.Sprite("assets/sprites/kenny_dungeon_pack/Isometric/stone_E.png", self.SCALE_FACTOR)
        return self.sprite_at(tile, x, y)

    def dude_at(self, x: int, y: int) -> arcade.Sprite:
        dude = arcade.Sprite("assets/sprites/kenny_dungeon_pack/Characters/Male/Male_0_Idle0.png", self.SCALE_FACTOR)
        return self.sprite_at(dude, x, y)
        
    def sprite_at(self, sprite: arcade.Sprite, x: int, y: int) -> arcade.Sprite:
        offset = self.grid_offset(x, y)
        sprite.center_x, sprite.center_y = self.get_xy_section_relative(
            self.width/2 + offset[0],
            self.Y_OFFSET + self.height/10 + offset[1],
        )
        return sprite

    def on_update(self, delta_time: float):
        self.init_dudes()

    def on_draw(self):
        self.manager.draw()
        self.tile_sprite_list.draw()
        self.dudes_sprite_list.draw()
        
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.manager.children[0][0].resize(width=width - 2, height=height - self.bottom)

    def set_encounter(self, event: dict) -> None:
        encounter_room = event.get("new_encounter", None)
        if encounter_room:
            self.encounter_room = encounter_room
            self.init_dudes()

    def init_dudes(self):
        if self.encounter_room is None:
            return
        self.dudes_sprite_list = arcade.SpriteList()
        for dude in self.encounter_room.occupants:
            self.dudes_sprite_list.append(
                self.dude_at(*dude.locatable.location)
            )