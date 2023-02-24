import arcade
from arcade.gui import UIManager
from arcade.gui.widgets import UIWidget
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.gui.window_data import WindowData
from src.gui.gui_utils import ScrollWindow, Cycle
from src.gui.buttons import CommandBarMixin
from src.gui.ui_styles import ADVENTURE_STYLE


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

    @property
    def command_bar(self) -> list[UIFlatButton]:
        return self.style_command_bar(buttons=self.buttons)

    def flush(self):
        self.manager = UIManager()
    
    def setup(self) -> None:
        """
        Can be called whenever the command bar should be prepared with buttons.
        Typically in a View's on_show_view, but can also be in response to a UIEvent if that event changes the available buttons.
        """
        self.compose_command_bar(self.manager, self.command_bar)

    def on_draw(self) -> None:
        self.manager.draw()

    def compose_command_bar(
        self, manager: UIManager, buttons: list[UIFlatButton]
    ) -> None:
        """
        Attaches the root node of the layout to the provided manager.
        Buttons are attached to the UIBoxLayout, which is the child of the root node.

        Args:
            manager (UIManager): The UIManager of a View which wants to have a command bar.
            buttons (list[UIFlatButton]): An array of UIFlatButtons with their own handlers already attached.
        """
        anchor = manager.add(UIAnchorLayout())
        command_box = UIBoxLayout(
            vertical=False,
            height=self.height,
            children=buttons,
            size_hint=(1, None),
        ).with_padding()

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            child=command_box,
        )

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
            button.with_border(width=2, color=arcade.color.GOLDENROD)

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

    def flush(self):
        self.manager = UIManager()
    
    def setup(self) -> None:
        self.compose_info_bar()

    def compose_info_bar(self) -> None:
        """
        Attaches the root node of the layout to the provided manager.
        Buttons are attached to the UIBoxLayout, which is the child of the root node.

        Args:
            manager (UIManager): The UIManager of a View which wants to have a command bar.
            buttons (list[UIFlatButton]): An array of UIFlatButtons with their own handlers already attached.
        """
        anchor = self.manager.add(UIAnchorLayout())
        command_box = (
            UIBoxLayout(
                vertical=True,
                height=self.height,
                size_hint=(1, None),
                align="top",
                children=self.texts,
            )
            .with_padding(top=10)
            .with_border(color=arcade.color.RED_DEVIL)
        )

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=self.bottom,
            child=command_box,
        )

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.width = width


def _entity_labels_with_cost(scroll_window: ScrollWindow) -> tuple[UIWidget, ...]:
    """Returns a tuple of UILabels which can be attached to a UILayout

    Args:
        scroll_window (ScrollWindow): ScrollWindow containing an array of entities with names and costs.

    Returns:
        tuple[UIWidget]: Tuple of UILabels. Can simply be attached to the children parameter of a UILayout.
    """
    return tuple(
        map(
            lambda entity: UILabel(
                text=f"{entity.name.name_and_title}: {entity.cost} gp",
                width=WindowData.width,
                font_size=18,
                font_name=WindowData.font,
                align="center",
                size_hint=(0.75, None),
            ).with_border(color=arcade.color.GENERIC_VIRIDIAN),
            scroll_window.items,
        )
    )

def _highlight_selection(scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]) -> None:
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
        
def _clear_highlight_selection(scroll_window: ScrollWindow, labels: tuple[UIWidget, ...]) -> None:
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

def _create_colored_UILabel_header(
    header_string: str, color: tuple[int, int, int, int]
) -> UILabel:
    return UILabel(
        text=f"{header_string}",
        width=WindowData.width,
        height=50,
        font_size=25,
        font_name=WindowData.font,
        align="center",
        size_hint=(1, None),
        text_color=color,
    )


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
        self.recruits_labels: tuple[UIWidget] = _entity_labels_with_cost(
            self.recruitment_scroll_window
        )
        self.header = _create_colored_UILabel_header(
            "Mercenaries For Hire!", arcade.color.GO_GREEN
        )
    
    def flush(self):
        self.manager = UIManager()

    def setup(self) -> None:
        self.recruitment_pane()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_draw(self):
        self.manager.draw()
        arcade.draw_lrtb_rectangle_outline(
            left=self.left,
            right=self.width,
            top=self.height,
            bottom=self.bottom,
            color=arcade.color.PURPLE_HEART,
        )

    def recruitment_pane(self) -> None:
        """
        Attaches the root node of the layout to the provided manager.
        UILabels are attached to the UIBoxLayouts, which are the children of the root node.

        Finally saves a reference to the recruits_box.children as self.recruits_box_children
        and applies selection highlighting for initial display of the UILabels.

        Args:
            manager (UIManager): The UIManager of a View which wants to have a command bar.
            buttons (list[UIFlatButton]): An array of UIFlatButtons with their own handlers already attached.
        """
        anchor = self.manager.add(UIAnchorLayout())

        header_box = UIBoxLayout(
            vertical=True,
            height=self.height,
            children=[self.header],
            size_hint=(1, 1),
        ).with_padding(top=10)

        recruits_box = UIBoxLayout(
            vertical=True,
            height=self.height,
            children=self.recruits_labels,
            size_hint=(1, 1),
            space_between=5,
        ).with_padding(top=50)

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            child=header_box,
        )

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            child=recruits_box,
        )

        self.recruits_box_children = self.manager.children[0][0].children[1].children

        _highlight_selection(self.recruitment_scroll_window, self.recruits_box_children)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.height = height - self.margin
        self.width = width - self.margin

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.X:
            print(
                self.manager.children[0][0]
                .children[1]
                .children[self.recruitment_scroll_window.position.pos]
                .label.color
            )

        if symbol == arcade.key.UP:
            """
            Decrement the recruitment_scroll_window.position.pos
            ie. move selection position up in the UI.
            """
            self.recruitment_scroll_window.decr_selection()
            _highlight_selection(
                self.recruitment_scroll_window,
                self.recruits_box_children,
            )
            self.manager.trigger_render()

        if symbol == arcade.key.DOWN:
            """
            Increment the recruitment_scroll_window.position.pos
            ie. move selection position down in the UI.
            """
            self.recruitment_scroll_window.incr_selection()
            _highlight_selection(
                self.recruitment_scroll_window,
                self.recruits_box_children,
            )
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
                highlighted_label = self.recruits_box_children[
                    self.recruitment_scroll_window.position.pos
                ]

                # Remove the UILabel from UIBoxLayout and pop the corresponding item from the recruitment_scroll_window.
                self.manager.children[0][0].children[1].remove(highlighted_label)
                self.recruitment_scroll_window.pop()

                # Update state
                self.recruits_box_children = (
                    self.manager.children[0][0].children[1].children
                )

                # Ensure highlighting carries over to the now selected recruit.
                _highlight_selection(
                    self.recruitment_scroll_window,
                    self.recruits_box_children,
                )

                self.manager.trigger_render()


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

        self.roster_header = _create_colored_UILabel_header("Roster", arcade.color.BYZANTIUM)
        self.team_header = _create_colored_UILabel_header("Team", arcade.color.BRASS)

        self.roster_labels: tuple[UIWidget] = _entity_labels_with_cost(
            self.roster_scroll_window
        )
        self.team_labels: tuple[UIWidget] = _entity_labels_with_cost(
            self.team_scroll_window
        )

    # def on_update(self, delta_time: float):
    #     print(delta_time)
        
    def flush(self):
        self.manager = UIManager()
        
        self.roster_labels: tuple[UIWidget] = _entity_labels_with_cost(
            self.roster_scroll_window
        )
        self.team_labels: tuple[UIWidget] = _entity_labels_with_cost(
            self.team_scroll_window
        )
    
    def on_draw(self):
        self.manager.draw()
        self.highlight_pane()

    def setup(self):
        # self.width = WindowData.width - 2,
        # self.height = WindowData.height - 2,
        self.roster_pane()
        self.team_pane()

    def highlight_pane(self):
        if self.pane_selector.pos == self.pane_id[0]:
            self.left = 0
            right = self.width / 2

            if len(self.team_box_children) > 0:
                _clear_highlight_selection(self.team_scroll_window, self.team_box_children)
                
            if len(self.roster_box_children) > 0:
                _highlight_selection(self.roster_scroll_window, self.roster_box_children)

            
        if self.pane_selector.pos == self.pane_id[1]:
            self.left = self.width / 2
            right = self.width
            
            if len(self.roster_box_children) > 0:
                _clear_highlight_selection(self.roster_scroll_window, self.roster_box_children)
                
            if len(self.team_box_children) > 0:
                _highlight_selection(self.team_scroll_window, self.team_box_children)

        arcade.draw_lrtb_rectangle_outline(
            left=self.left,
            right=right,
            top=self.height,
            bottom=self.bottom,
            color=arcade.color.ATOMIC_TANGERINE,
        )
        self.manager.trigger_render()

    def roster_pane(self):
        """
        Creates two UIBoxLayouts and attaches them to UIManager.
        First UIBoxLayout contains the pane header, the second is for the UILabels representing mercenaries currently on the Roster.
        """
        anchor = self.manager.add(UIAnchorLayout(size_hint=(0.5, 1)))

        header_box = UIBoxLayout(
            vertical=True,
            # height=self.height,
            children=[self.roster_header],
            size_hint=(1, 1),
        ).with_padding(top=10)

        roster_box = UIBoxLayout(
            vertical=True,
            # height=self.height,
            children=self.roster_labels,
            size_hint=(1, 1),
            space_between=5,
        ).with_padding(top=50)

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            child=header_box,
        )

        anchor.add(
            anchor_x="center_x",
            anchor_y="bottom",
            child=roster_box,
        )
        
        self.roster_box_children = self.manager.children[0][0].children[1].children
        
        if self.pane_selector.pos == self.pane_id[0]:
            _highlight_selection(self.roster_scroll_window, self.roster_box_children)
        
    def team_pane(self):
        """
        Creates two UIBoxLayouts and attaches them to UIManager
        First UIBoxLayout contains the pane header, the second is for the UILabels representing mercenaries assigned to the team.
        """
        anchor = self.manager.add(UIAnchorLayout(size_hint=(1, 1)))

        header_box = UIBoxLayout(
            vertical=True,
            height=self.height,
            children=[self.team_header],
            size_hint=(0.5, 1),
        ).with_padding(top=10)

        team_box = UIBoxLayout(
            vertical=True,
            height=self.height,
            children=self.team_labels,
            size_hint=(0.5, 1),
            space_between=5,
        ).with_padding(
            top=50
        )

        anchor.add(
            anchor_x="right",
            anchor_y="bottom",
            child=header_box,
        )

        anchor.add(
            anchor_x="right",
            anchor_y="bottom",
            child=team_box,
        )
        self.team_box_children = self.manager.children[0][1].children[1].children     
        # _highlight_selection(self.team_scroll_window, self.team_box_children)
        
    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.height = height - 2
        self.width = width - 2

    def on_key_press(self, symbol: int, modifiers: int):
        """
        Left / Right changes focus between Roster & Team panes: 
        Up / Down to change label selection and apply highlighting
        Enter assigns the highlighted member to the team or the roster
        """
        match symbol:
            case arcade.key.LEFT:
                self.pane_selector.decr()
                
            case arcade.key.RIGHT:
                self.pane_selector.incr()
            
            case arcade.key.UP:
                if self.pane_selector.pos == self.pane_id[0]:
                    self.roster_scroll_window.decr_selection()
                    _highlight_selection(
                        self.roster_scroll_window,
                        self.roster_box_children,
                    )
                    self.manager.trigger_render()

                if self.pane_selector.pos == self.pane_id[1]:
                    self.team_scroll_window.decr_selection()
                    _highlight_selection(
                        self.team_scroll_window,
                        self.team_box_children,
                    )
                    self.manager.trigger_render()

            case arcade.key.DOWN:
                if self.pane_selector.pos == self.pane_id[0]:
                    self.roster_scroll_window.incr_selection()
                    _highlight_selection(
                        self.roster_scroll_window,
                        self.roster_box_children,
                    )
                    self.manager.trigger_render()
                
                if self.pane_selector.pos == self.pane_id[1]:
                    self.team_scroll_window.incr_selection()
                    _highlight_selection(
                        self.team_scroll_window,
                        self.team_box_children,
                    )
                    self.manager.trigger_render()

            case arcade.key.ENTER:
                if (
                    self.pane_selector.pos == self.pane_id[0]
                    and len(self.roster_scroll_window.items) > 0
                ):
                    # Move merc from ROSTER to TEAM. Increase Cycle.length for team, decrease Cycle.length for roster.
                    # Assign to Team & Remove from Roster.
                    self.team_scroll_window.append(
                        self.roster_scroll_window.selection
                    )
                    eng.game_state.guild.team.assign_to_team(
                        self.roster_scroll_window.selection
                    )
                    self.roster_scroll_window.pop()

                    # Update Engine state.
                    eng.game_state.guild.roster = self.roster_scroll_window.items
                    eng.game_state.guild.team.members = self.team_scroll_window.items
                    self.manager.disable()
                    self.flush()
                    self.setup()
                    self.manager.enable()
                    self.manager.trigger_render()
                    
                if (
                    self.pane_selector.pos == self.pane_id[1]
                    and len(self.team_scroll_window.items) > 0
                ):
                    # Move merc from TEAM to ROSTER
                    self.roster_scroll_window.append(
                        self.team_scroll_window.selection
                    )

                    # Remove from Team array
                    self.team_scroll_window.pop()

                    # Update Engine state.
                    eng.game_state.guild.roster = self.roster_scroll_window.items
                    eng.game_state.guild.team.members = self.team_scroll_window.items
                    self.manager.disable()
                    self.flush()
                    self.setup()
                    self.manager.enable()
                    _highlight_selection(self.team_scroll_window, self.team_box_children)
                    self.manager.trigger_render()