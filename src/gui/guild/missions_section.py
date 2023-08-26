import arcade
from arcade.gui import UIManager

from src.config import font_sizes
from src.gui.components.layouts import (
    box_containing_horizontal_label_pair,
    create_colored_shadowed_UILabel_header,
)
from src.gui.components.scroll_window import Cycle
from src.gui.guild.missions_components import mission_boxes
from src.textures.texture_data import SingleTextureSpecs


class MissionCards:
    TOP = 0
    MIDDLE = 1
    BOTTOM = 2


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
            create_colored_shadowed_UILabel_header(
                header_string=self.missions[0].description,
                font_size=font_sizes.SUBTITLE,
                color=arcade.color.RED,
                height=45,
            ),
            create_colored_shadowed_UILabel_header(
                header_string=self.missions[1].description,
                font_size=font_sizes.SUBTITLE,
                color=arcade.color.GRAY,
                height=45,
            ),
            create_colored_shadowed_UILabel_header(
                header_string=self.missions[2].description,
                font_size=font_sizes.SUBTITLE,
                color=arcade.color.GRAY,
                height=45,
            ),
        )

        labels = (
            (
                *headers[0],
                box_containing_horizontal_label_pair(
                    (
                        ("Boss:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[0].boss.name.name_and_title,
                            "left",
                            font_sizes.BODY,
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
                        ("Rewards:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[0].peek_reward(),
                            "left",
                            font_sizes.BODY,
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
                        ("Boss:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[1].boss.name.name_and_title,
                            "left",
                            font_sizes.BODY,
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
                        ("Rewards:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[1].peek_reward(),
                            "left",
                            font_sizes.BODY,
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
                        ("Boss:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[2].boss.name.name_and_title,
                            "left",
                            font_sizes.BODY,
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
                        ("Rewards:", "left", font_sizes.BODY, arcade.color.GOLD),
                        (
                            self.missions[2].peek_reward(),
                            "left",
                            font_sizes.BODY,
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

        tex_references = []
        banner_references = []
        self.manager.add(
            mission_boxes(
                self.bottom,
                self.height,
                content_top=labels[0],
                content_mid=labels[1],
                content_btm=labels[2],
                panel_highlighted=SingleTextureSpecs.panel_highlighted.loaded,
                panel_darkened=SingleTextureSpecs.panel_darkened.loaded,
                tex_reference_buffer=tex_references,
                banner_reference_buffer=banner_references,
            ),
        )

        self.highlighted_tex, self.darkened_tex = [
            ref.texture for ref in tex_references[:2]
        ]

        self.top_pane, self.mid_pane, self.bottom_pane = tex_references
        self.tex_panes = tex_references

        self.highlighted_banner, self.darkened_banner = [
            ref.texture for ref in banner_references[:2]
        ]

        self.banners = banner_references

        self.top_label = self.manager.children[0][0].children[9].children[0]
        self.mid_label = self.manager.children[0][0].children[10].children[0]
        self.btm_label = self.manager.children[0][0].children[11].children[0]

    def highlight_states(self) -> tuple[int, int, int]:
        return (
            # highlighted
            self.mission_selection.pos,
            # normal
            (self.mission_selection.pos + 1) % 3,
            (self.mission_selection.pos + 2) % 3,
        )

    def _highlight_selected_pane(self, highlighted, normal, _normal):
        self.tex_panes[highlighted].texture = self.highlighted_tex
        self.tex_panes[normal].texture = self.darkened_tex
        self.tex_panes[_normal].texture = self.darkened_tex

        self.banners[highlighted].texture = self.highlighted_banner
        self.banners[normal].texture = self.darkened_banner
        self.banners[_normal].texture = self.darkened_banner

        if highlighted == 0:
            self.top_label.label.color = arcade.color.RED
            self.mid_label.label.color = arcade.color.GRAY
            self.btm_label.label.color = arcade.color.GRAY

        elif highlighted == 1:
            self.top_label.label.color = arcade.color.GRAY
            self.mid_label.label.color = arcade.color.RED
            self.btm_label.label.color = arcade.color.GRAY

        elif highlighted == 2:
            self.top_label.label.color = arcade.color.GRAY
            self.mid_label.label.color = arcade.color.GRAY
            self.btm_label.label.color = arcade.color.RED

    def scroll_mission_selection(self):
        match self.mission_selection.pos:
            case MissionCards.TOP:
                # self.manager.children[0][0].children[0].
                highlight, normal, _normal = self.highlight_states()
                self._highlight_selected_pane(highlight, normal, _normal)

            case MissionCards.MIDDLE:
                highlight, normal, _normal = self.highlight_states()
                self._highlight_selected_pane(highlight, normal, _normal)

            case MissionCards.BOTTOM:
                highlight, normal, _normal = self.highlight_states()
                self._highlight_selected_pane(highlight, normal, _normal)

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
                self.manager.trigger_render()

            case arcade.key.DOWN:
                self.mission_selection.incr()
                self.scroll_mission_selection()
                self.manager.trigger_render()
