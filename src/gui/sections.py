import arcade
from arcade.gui import UIManager
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.widgets.text import UILabel
from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.gui.buttons import CommandBarMixin
from src.gui.combat_screen import CombatScreen
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
from src.gui.selection_texture_enums import SelectionCursor
from src.gui.states import MissionCards
from src.gui.ui_styles import ADVENTURE_STYLE
from src.gui.window_data import WindowData
from src.utils.pathing.grid_utils import Node


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


def do_nothing():
    pass


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
    TILE_BASE_DIMS = (17, 16)
    SET_ENCOUNTER_HANDLER_ID = "set_encounter"
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
        self._original_dims = width, height

        # if 800 <= WindowData.width <= 1080 and 600 <= WindowData.height <= 720:
        #     self.SCALE_FACTOR = 0.2
        #
        # if 1920 >= WindowData.width >= 1080 >= WindowData.height >= 720:
        #     self.SCALE_FACTOR = 0.25

        self.tile_sprite_list = arcade.SpriteList()
        scale = 1
        for x in range(9, -1, -1):
            for y in range(9, -1, -1):
                self.tile_sprite_list.append(self.floor_tile_at(x, y, scale))
                wall_sprite = None
                if y == 9 and x < 9:
                    wall_sprite = self.wall_tile_at(
                        x, y, Node(0, 1), scale
                    )  # top right wall
                if x == 9 and y < 9:
                    wall_sprite = self.wall_tile_at(x, y, Node(1, 0), scale)
                if x == 9 and y == 9:
                    wall_sprites = self.wall_tile_at(x, y, Node(1, 1), scale)
                if wall_sprite:
                    self.tile_sprite_list.append(*wall_sprite)
                if wall_sprites:
                    for wall in wall_sprites:
                        self.tile_sprite_list.append(wall)
                    # Ensure we don't try to reappend the sprites.
                    wall_sprites = None

        self.dudes_sprite_list = arcade.SpriteList()
        self.combat_screen = CombatScreen()
        self.grid_camera = arcade.Camera()
        self.other_camera = arcade.Camera()
        self._subscribe_to_events()
        self.selected_path_sprites = self.init_path()

    @classmethod
    def init_path(cls) -> arcade.SpriteList:
        selected_path_sprites = arcade.SpriteList()
        selected_path_sprites.append(
            arcade.Sprite(WindowData.indicators[SelectionCursor.GREEN.value])
        )
        for _ in range(1, 19):
            sprite_tex = WindowData.indicators[SelectionCursor.GOLD_EDGE.value]
            sprite = arcade.Sprite(sprite_tex, scale=WindowData.scale[1])
            selected_path_sprites.append(sprite)

        selected_path_sprites.append(
            arcade.Sprite(WindowData.indicators[SelectionCursor.RED.value])
        )

        return selected_path_sprites

    def _subscribe_to_events(self):
        eng.combat_dispatcher.volatile_subscribe(
            topic="new_encounter",
            handler_id="CombatGrid.set_encounter",
            handler=self.set_encounter,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="move",
            handler_id="CombatGrid.update_dudes",
            handler=self.update_dudes,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="cleanup",
            handler_id="CombatGrid.clear_occupants",
            handler=self.clear_occupants,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="attack",
            handler_id="CombatGrid.swap_textures_for_attack",
            handler=self.idle_or_attack,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="dead",
            handler_id="CombatGrid.clear_dead_sprites",
            handler=self.clear_dead_sprites,
        )

    def clear_occupants(self, event):
        encounter = event["cleanup"]
        for occupant in encounter.occupants:
            if occupant.fighter.is_enemy == False:
                encounter.remove(occupant)

    def scaling(self) -> Vec2:
        return Vec2(
            self.width / self._original_dims[0],
            self.height / self._original_dims[1],
        )

    def grid_offset(self, x: int, y: int) -> Vec2:
        grid_scale = 0.75
        sx, sy = WindowData.scale
        constant_scale = grid_scale * self.TILE_BASE_DIMS[0] * self.SCALE_FACTOR
        return Vec2(
            (x - y) * sx * 13,
            (x + y) * sy * 5,
        ) * constant_scale + Vec2(self.width / 2, 7 * self.height / 8)

    def grid_loc(self, v: Vec2) -> Node:
        v2 = v - Vec2(self.width / 2, 7 * self.height / 8)
        sx, sy = self.scaling()
        grid_scale = 0.75
        v3 = Vec2(  # (x-y, x+y)
            v2.x
            / (sx * grid_scale * self.TILE_BASE_DIMS[0] * self.SCALE_FACTOR * (13)),
            v2.y / (sy * grid_scale * self.TILE_BASE_DIMS[0] * self.SCALE_FACTOR * (5)),
        )

        node_x = (v3.x + v3.y) / 2
        node_y = (-v3.x + v3.y) / 2
        return Node(
            x=round(node_x),
            y=round(node_y),
        )

    def wall_tile_at(
        self, x: int, y: int, orientation: Node, scale_factor=1
    ) -> tuple[arcade.Sprite, ...]:
        scale = 5 * scale_factor
        wall = self.sprite_at(arcade.Sprite(scale=scale), x, y)
        if orientation == Node(1, 0):
            # Right / East Walls
            wall.center_y += 45
            wall.center_x += 40
            sprites = (wall,)

        elif orientation == Node(1, 1):
            # Three wall sprites for the corner
            left = self.sprite_at(arcade.Sprite(scale=scale), x, y)
            right = self.sprite_at(arcade.Sprite(scale=scale), x, y)
            top = self.sprite_at(arcade.Sprite(scale=scale), x, y)
            left.center_y += 45
            left.center_x -= 40
            right.center_y += 45
            right.center_x += 40
            top.center_y += 100
            sprites = (left, right, top)

        else:
            # Left / West Walls
            wall.center_y += 45
            wall.center_x -= 40
            sprites = (wall,)

        for s in sprites:
            s.texture = WindowData.tiles[89]

        return sprites

    def floor_tile_at(self, x: int, y: int, scale=1) -> arcade.Sprite:
        tile = arcade.Sprite(scale=5 * scale)
        tile.texture = WindowData.tiles[100]

        return self.sprite_at(tile, x, y)

    def sprite_at(self, sprite: arcade.Sprite, x: int, y: int) -> arcade.Sprite:
        offset = self.grid_offset(x, y)
        sprite.center_x, sprite.center_y = offset
        return sprite

    def on_update(self, delta_time: float):
        eng.update_clock -= delta_time

        call_hook = True
        if not eng.awaiting_input:
            hook = eng.next_combat_action
        else:
            hook = do_nothing

        self.dudes_sprite_list.update_animation(delta_time=delta_time)

        if eng.update_clock < 0:
            eng.reset_update_clock()
            if call_hook:
                call_hook = hook()

    def on_draw(self):
        self.grid_camera.use()

        self.tile_sprite_list.draw(pixelated=True)
        self.dudes_sprite_list.draw(pixelated=True)
        self.selected_path_sprites.draw(pixelated=True)

        self.other_camera.use()

        if eng.awaiting_input:
            self.combat_screen.draw_turn_prompt()

        if eng.mission_in_progress == False:
            self.combat_screen.draw_turn_prompt()

        self.combat_screen.draw_message()
        self.combat_screen.draw_stats()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.grid_camera.set_viewport(
            (0, 0, width, height)
        )  # Stretch the sprites with the window resize
        self.other_camera.resize(
            viewport_width=width, viewport_height=height
        )  # Resize the camera displaying the combat text

    def set_encounter(self, event: dict) -> None:
        encounter_room = event.get("new_encounter", None)
        if encounter_room:
            self.encounter_room = encounter_room

            self.prepare_dude_sprites()

            self.update_dudes(event)

    def prepare_dude_sprites(self):
        """
        Constructs the sprite list with the appropriate sprites when starting a dungeon.
        Clears the sprite when entering a new room and reconstructs with new room member sprites.
        """
        if not self.dudes_sprite_list:
            self.dudes_sprite_list = arcade.SpriteList()
        else:
            self.dudes_sprite_list.clear()

        for dude in self.encounter_room.occupants:
            if dude.fighter.is_boss:
                dude.entity_sprite.sprite.scale = dude.entity_sprite.sprite.scale * 1.5

            dude.entity_sprite.sprite = self.sprite_at(
                dude.entity_sprite.sprite,
                dude.entity_sprite.sprite.center_x,
                dude.entity_sprite.sprite.center_y,
            )

            dude.entity_sprite.sprite.center_y += 15
            dude.entity_sprite.orient(dude.locatable.orientation)
            self.dudes_sprite_list.append(dude.entity_sprite.sprite)

    def update_dudes(self, _: dict) -> None:
        self._update_dudes()

    def _update_dudes(self):
        """
        Check if any sprites associated to a dead entity are still in the list, if so remove them.
        Iterate over the occupants of the current room and update the positional information of their sprites as necessary.
        Sort the sprite list such that sprites higher in screen space are drawn first and then overlapped by lower sprites.
        """
        if self.encounter_room is None:
            return

        # self.clear_dead_sprites()
        for dude in self.encounter_room.occupants:
            offset = self.grid_offset(
                dude.locatable.location.x, dude.locatable.location.y
            )
            dude.entity_sprite.sprite.center_x = offset.x
            dude.entity_sprite.sprite.center_y = offset.y
            dude.entity_sprite.sprite.center_y += 15
            dude.entity_sprite.orient(dude.locatable.orientation)
        self.dudes_sprite_list.sort(key=lambda y: y.position[1], reverse=True)

    def show_path(self, current: tuple[Node]):
        head = (0,)
        body = tuple(range(1, len(current) - 1))
        tail = (19,)
        rest = range(len(current) - 1, 19)

        visible = [*head, *body, *tail]
        invisible = rest

        for i, sprite in enumerate(self.selected_path_sprites):
            if i in visible:
                node_idx = i if i in head + body else -1
                node = current[node_idx]
                position = self.grid_offset(*node)
                sprite.visible = True
                sprite.center_x, sprite.center_y = position.x, position.y
            elif i in invisible:
                sprite.visible = False

        print(current)

    def hide_path(self):
        for sprite in self.selected_path_sprites:
            sprite.visible = False

    def idle_or_attack(self, event):
        dude = event["attack"]
        dude.entity_sprite.swap_idle_and_attack_textures()

    def clear_dead_sprites(self, event):
        """
        If a sprite is associated to a dead entity, remove the sprite from the sprite list.
        """
        dead_dude = event["dead"]
        self.dudes_sprite_list.pop(
            self.dudes_sprite_list.index(dead_dude.owner.entity_sprite.sprite)
        )
