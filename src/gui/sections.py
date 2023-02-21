import arcade
from arcade.gui import UIManager
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel, UITextArea
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.gui.window_data import WindowData
from src.gui.gui_utils import ScrollWindow
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


def _entity_labels_with_cost(scroll_window):
    """
    Prototyping construction of hireable merc names as an array of UILabels for RecruitmentSection UIManager.
    """
    labels = []

    for entity in scroll_window.items:
        label = UILabel(
            text=f"{entity.name.name_and_title}: {entity.cost} gp",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(0.5, None),
        ).with_border(color=arcade.color.GENERIC_VIRIDIAN)

        labels.append(label)

    return labels


class RecruitmentPaneSection(arcade.Section):
    labels: list[UILabel]
    merc: Entity

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
        self.labels = _entity_labels_with_cost(self.recruitment_scroll_window)
        self.margin = 2
        self.header = UILabel(
            text="Mercenaries For Hire!",
            width=WindowData.width,
            height=50,
            font_size=25,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
            text_color=arcade.color.GO_GREEN,
        )

    def setup(self) -> None:
        # self._entity_labels()
        self.recruitment_pane()
        print(self.view.info_pane_section.texts[1].label.text)

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
            children=self.labels,
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

        # Set the color of the label corresponding to the recruitment_scroll_window.position.pos
        # to indicate the initial selection when this section is enabled.
        self.manager.children[0][0].children[1].children[
            self.recruitment_scroll_window.position.pos
        ].label.color = arcade.color.GOLD

        # This is how you get to the children.
        # Investigate for refactoring selection highlighting
        # for children in self.manager.children[0]:
        #     for child in children.children[1].children:
        #         print(child.text)

    def highlight_selection(self):
        """Forgive me Father for I have sinned.

        Highlight the currently selected entry in the recruitment pane with a color and ">>" selection mark prepended to the text
        """
        for child in self.manager.children[0][0].children[1].children:
            child.label.color = arcade.color.WHITE
            child.label.text = f"{self.recruitment_scroll_window.items[self.manager.children[0][0].children[1].children.index(child)].name.name_and_title}: {self.recruitment_scroll_window.items[self.manager.children[0][0].children[1].children.index(child)].cost} gp"

        self.manager.children[0][0].children[1].children[
            self.recruitment_scroll_window.position.pos
        ].label.color = arcade.color.GOLD

        self.manager.children[0][0].children[1].children[
            self.recruitment_scroll_window.position.pos
        ].label.text = f">> {self.recruitment_scroll_window.items[self.recruitment_scroll_window.position.pos].name.name_and_title}: {self.recruitment_scroll_window.items[self.recruitment_scroll_window.position.pos].cost} gp"

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

            self.highlight_selection()
            self.manager.trigger_render()

        if symbol == arcade.key.DOWN:
            """
            Increment the recruitment_scroll_window.position.pos
            ie. move selection position down in the UI.
            """
            self.recruitment_scroll_window.incr_selection()

            self.highlight_selection()
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
                highlighted_label = (
                    self.manager.children[0][0]
                    .children[1]
                    .children[self.recruitment_scroll_window.position.pos]
                )

                # Remove the UILabel from UIBoxLayout and pop the corresponding item from the recruitment_scroll_window.
                self.manager.children[0][0].children[1].remove(highlighted_label)
                self.recruitment_scroll_window.pop()

                # Carry the selection highlighting to the next selection after removing the current selection.
                self.manager.children[0][0].children[1].children[
                    self.recruitment_scroll_window.position.pos
                ].label.color = arcade.color.GOLD
                self.manager.trigger_render()
