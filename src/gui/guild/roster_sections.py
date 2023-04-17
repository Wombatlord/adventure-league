import arcade
from arcade.gui import UIManager, UIWidget

from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.gui.components.layouts import horizontal_box_pair, single_box
from src.gui.components.scroll_window import Cycle, ScrollWindow
from src.gui.guild.recruitment_components import entity_labels_with_cost
from src.gui.guild.roster_components import entity_labels_names_only
from src.textures.pixelated_nine_patch import PixelatedNinePatch
from src.textures.texture_data import SingleTextureSpecs, SpriteSheetSpecs


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
            entity_label.label._text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}: {scroll_window.items[entity_labels.index(entity_label)].cost} gp"

        # Set selected entity_label color to gold and text to selection string
        entity_labels[scroll_window.position.pos].label.color = arcade.color.GOLD
        entity_labels[
            scroll_window.position.pos
        ].label._text = f">> {entity_labels[scroll_window.position.pos].label._text}"


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
        self.panel_texture = SingleTextureSpecs.panel_highlighted.loaded
        self.recruitment_scroll_window = ScrollWindow(
            eng.game_state.entity_pool.pool, 10, 10
        )
        self.banner = arcade.Sprite(
            SingleTextureSpecs.mercenaries_banner.loaded,
            center_x=width / 2,
            center_y=height - 50,
            scale=2,
        )
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.banner)

        self.update_ui()

    @property
    def selected_entity(self) -> Entity | None:
        return self.recruitment_scroll_window.selection

    def update_ui(self):
        self.manager = UIManager()

        # self.header = create_colored_UILabel_header(
        #     "Mercenaries For Hire!",
        #     arcade.color.GO_GREEN,
        #     font_size=font_sizes.TITLE,
        #     height=55,
        # )
        self.recruits_labels: tuple[UIWidget] = entity_labels_with_cost(
            self.recruitment_scroll_window
        )

        content = (*self.recruits_labels,)

        self.manager.add(
            single_box(
                self.bottom,
                self.height - self.bottom,
                content,
                padding=(85, 0, 0, 0),
                panel=self.panel_texture,
            )
        )

        _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)
        self.manager.trigger_render()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_draw(self):
        self.manager.draw()
        self.sprite_list.draw(pixelated=True)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.manager.children[0][0].resize(width=width, height=(height - self.bottom))
        self.width = width
        self.height = height
        self.update_ui()
        self.banner.center_x = width / 2
        self.banner.center_y = height - 50

    def recruitment_limit_not_reached(self):
        current_member_amount = len(eng.game_state.guild.roster) + len(
            eng.game_state.team.members
        )
        return current_member_amount < eng.game_state.guild.roster_limit

    def on_select(self):
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
        self.manager.children[0][0].children[1].remove(highlighted_label)
        self.recruitment_scroll_window.pop()

        # Update state
        self.recruits_labels = self.manager.children[0][0].children[1].children[1:]

        # Ensure highlighting carries over to the now selected recruit.
        _highlight_selection(
            self.recruitment_scroll_window,
            self.recruits_labels,
        )

        # self.manager.trigger_render()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.UP:
            """
            Decrement the recruitment_scroll_window.position.pos
            ie. move selection position up in the UI.
            """
            self.recruitment_scroll_window.decr_selection()
            _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)
            # self.manager.trigger_render()

        if symbol == arcade.key.DOWN:
            """
            Increment the recruitment_scroll_window.position.pos
            ie. move selection position down in the UI.
            """
            self.recruitment_scroll_window.incr_selection()
            _highlight_selection(self.recruitment_scroll_window, self.recruits_labels)
            # self.manager.trigger_render()

        if symbol == arcade.key.ENTER:
            # If the total amount of guild members does not equal the roster_limit, recruit the selected mercenary to the guild.
            if self.recruitment_limit_not_reached():
                self.on_select()

        self.update_ui()


def _highlight_selection_text(
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
    if not labels:
        return

    entity_labels = labels
    label = entity_labels[scroll_window.position.pos]

    # Set all entity_label colors to white and text to non-selected string.
    for entity_label in entity_labels:
        entity_label.label.color = arcade.color.WHITE
        entity_label.label._text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}"

    # Set selected entity_label color to gold and text to selection string
    label.label.color = arcade.color.GOLD
    label.label._text = f">> {entity_labels[scroll_window.position.pos].label._text}"


def _normal_selection_text(
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
        entity_label.label.color = arcade.color.GRAY
        entity_label.label._text = f"{scroll_window.items[entity_labels.index(entity_label)].name.name_and_title}"


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

        self.init_nine_patch_pair()
        self.roster_scroll_window = ScrollWindow(eng.game_state.guild.roster, 10, 10)
        self.team_scroll_window = ScrollWindow(
            eng.game_state.guild.team.members, 10, 10
        )
        self.sprite_list = arcade.SpriteList()
        self.roster_banner = arcade.Sprite(
            SpriteSheetSpecs.banners.load_one(0),
            center_x=width / 4,
            center_y=height - 50,
            scale=2,
        )
        self.roster_banner.textures.append(SpriteSheetSpecs.banners.load_one(1))
        self.team_banner = arcade.Sprite(
            SpriteSheetSpecs.banners.load_one(3),
            center_x=width - width / 4,
            center_y=height - 50,
            scale=2,
        )
        self.team_banner.textures.append(SpriteSheetSpecs.banners.load_one(2))
        self.sprite_list.append(self.roster_banner)
        self.sprite_list.append(self.team_banner)
        # Indicates whether Roster or Team pane is the active pane.
        self.pane_selector = Cycle(2)
        self.tex_idx = Cycle(2)
        self.update_ui()

    @property
    def selected_menu(self) -> ScrollWindow:
        return [self.roster_scroll_window, self.team_scroll_window][self.pane_selector]

    @property
    def selected_entity(self) -> Entity | None:
        return self.selected_menu.selection

    def swap_banner_textures(self):
        self.tex_idx.incr()
        for sprite in self.sprite_list:
            sprite.texture = sprite.textures[self.tex_idx]

    def update_labels(self):
        self.roster_labels: tuple[UIWidget] = entity_labels_names_only(
            self.roster_scroll_window
        )
        self.team_labels: tuple[UIWidget] = entity_labels_names_only(
            self.team_scroll_window
        )

    def update_ui(self):
        self.sync_state()
        self.manager = UIManager()

        self.update_labels()

        self.roster_content = (*self.roster_labels,)
        self.team_content = (*self.team_labels,)

        references = []

        self.manager.add(
            horizontal_box_pair(
                self.bottom,
                self.height - self.bottom,
                self.roster_content,
                self.team_content,
                padding=(100, 0, 0, 0),
                panel_highlighted=self.panel_highlighted_texture,
                panel_darkened=self.panel_darkened_texture,
                tex_reference_buffer=references,
            )
        )

        self.highlighted_tex, self.darkened_tex = [ref.texture for ref in references]
        self.left_pane, self.right_pane = references
        self.tex_panes = references
        self.update_highlights()

    def init_nine_patch_pair(self):
        self.panel_highlighted_texture = SingleTextureSpecs.panel_highlighted.loaded
        self.panel_darkened_texture = SingleTextureSpecs.panel_darkened.loaded

        self.panel_highlighted = PixelatedNinePatch(
            left=15,
            right=15,
            bottom=15,
            top=15,
            texture=self.panel_highlighted_texture,
        )

        self.panel_darkened = PixelatedNinePatch(
            left=15,
            right=15,
            bottom=15,
            top=15,
            texture=self.panel_darkened_texture,
        )

    def highlight_states(self) -> tuple[int, int]:
        return (
            # highlighted
            self.pane_selector.pos,
            # normal
            (self.pane_selector.pos + 1) % 2,
        )

    def update_highlights(self):
        highlighted, normal = self.highlight_states()
        self._highlight_selected_pane(highlighted, normal)
        self._set_text_highlight(highlighted, normal)

        self.manager.trigger_render()

    def _highlight_selected_pane(self, highlighted, normal):
        self.tex_panes[highlighted].texture = self.highlighted_tex
        self.tex_panes[normal].texture = self.darkened_tex

    def _set_text_highlight(self, highlighted, normal):
        scroll_windows = [self.roster_scroll_window, self.team_scroll_window]
        labels = [self.roster_labels, self.team_labels]

        if labels[highlighted]:
            _highlight_selection_text(scroll_windows[highlighted], labels[highlighted])
        if labels[normal]:
            _normal_selection_text(scroll_windows[normal], labels[normal])

    def on_draw(self):
        self.manager.draw()
        self.sprite_list.draw(pixelated=True)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.height = height
        self.width = width
        self.update_ui()
        self.manager.children[0][0].resize(width=width, height=(height - self.bottom))
        self.update_banner_positions(width, height)

    def update_banner_positions(self, width, height):
        self.roster_banner.center_x = width / 4
        self.roster_banner.center_y = height - 50
        self.team_banner.center_x = width - width / 4
        self.team_banner.center_y = height - 50

    def on_select(self):
        """
        Update the model in response to a selection by the user. This should manage
        all game state change controlled by this view is here.
        """
        highlighted, normal = self.highlight_states()
        scroll_windows = [self.roster_scroll_window, self.team_scroll_window]

        item = scroll_windows[highlighted].pop()

        if scroll_windows[highlighted] == self.roster_scroll_window:
            eng.game_state.guild.team.assign_to_team(item)
        else:
            eng.game_state.guild.team.move_fighter_to_roster(item)

        scroll_windows[normal].append(item)

    def sync_state(self):
        """
        Query the model for the updated team/roster composition.
        This method is for reading the state from the model into the view.
        """
        self.roster_scroll_window.items = [*eng.game_state.guild.roster]
        self.team_scroll_window.items = [*eng.game_state.guild.team.members]

    def on_key_press(self, symbol: int, modifiers: int):
        """
        Left / Right changes focus between Roster & Team panes:
        Up / Down to change label selection and apply highlighting
        Enter assigns the highlighted member to the team or the roster
        """
        scroll_windows = [self.roster_scroll_window, self.team_scroll_window]
        labels = [self.roster_labels, self.team_labels]

        highlighted, _ = self.highlight_states()
        match symbol:
            case arcade.key.LEFT:
                self.pane_selector.decr()
                self.swap_banner_textures()
                self.update_highlights()

            case arcade.key.RIGHT:
                self.pane_selector.incr()
                self.swap_banner_textures()
                self.update_highlights()

            case arcade.key.UP:
                scroll_windows[highlighted].decr_selection()
                _highlight_selection_text(
                    scroll_windows[highlighted], labels[highlighted]
                )
                self.manager.trigger_render()

            case arcade.key.DOWN:
                scroll_windows[highlighted].incr_selection()
                _highlight_selection_text(
                    scroll_windows[highlighted], labels[highlighted]
                )
                self.manager.trigger_render()

            case arcade.key.ENTER:
                if scroll_windows[highlighted].items:
                    self.on_select()

            case _:
                # prevents pointless re-render on unbound keypress
                return

        self.update_ui()
