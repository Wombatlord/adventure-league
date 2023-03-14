import arcade
import arcade.color
import arcade.key
from arcade import Window
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.text import UILabel
from pyglet.math import Vec2

from src.engine.init_engine import eng
from src.gui.buttons import get_new_missions_button, nav_button
from src.gui.gui_components import box_containing_horizontal_label_pair
from src.gui.gui_utils import Cycle
from src.gui.sections import (
    CombatGridSection,
    CommandBarSection,
    InfoPaneSection,
    MissionsSection,
    RecruitmentPaneSection,
    RosterAndTeamPaneSection,
)
from src.gui.states import ViewStates
from src.gui.window_data import WindowData
from src.utils.input_capture import Selection
from src.utils.pathing.grid_utils import Node


class TitleView(arcade.View):
    def __init__(self, window: Window | None = None):
        super().__init__(window)
        self.background = WindowData.title_background
        self.title_y = -10
        self.start_y = -10

    def on_show_view(self):
        """Called when switching to this view"""
        pass

    def on_update(self, delta_time: float):
        if self.title_y < WindowData.height * 0.75:
            self.title_y += 5

        if (
            self.title_y == WindowData.height * 0.75
            and self.start_y < WindowData.height * 0.3
        ):
            self.start_y += 5

    def on_draw(self):
        """Draw the title screen"""
        self.clear()

        # Draw the background image
        arcade.draw_lrwh_rectangle_textured(
            0, 0, WindowData.width, WindowData.height, self.background
        )

        # Draw the scrolling title text. Scrolling is handled in self.on_update().
        arcade.draw_text(
            "ADVENTURE LEAGUE!",
            WindowData.width / 2,
            self.title_y,
            arcade.color.GOLD,
            font_name=WindowData.font,
            font_size=40,
            anchor_x="center",
        )

        arcade.draw_text(
            "Press G for a Guild View!",
            WindowData.width / 2,
            self.start_y,
            arcade.color.GOLDENROD,
            font_name=WindowData.font,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class GuildView(arcade.View):
    """Draw a view displaying information about a guild"""

    state = ViewStates.GUILD

    def __init__(self, window: Window = None):
        super().__init__(window)
        # InfoPane config.
        self.guild_label = UILabel(
            text=eng.game_state.guild.name,
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, None),
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=148,
            prevent_dispatch_view={False},
            margin=5,
            texts=[self.guild_label],
        )
        # CommandBar config
        self.buttons = [
            nav_button(MissionsView, "Missions"),
            nav_button(RosterView, "Roster"),
            get_new_missions_button(),
        ]
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        # Add sections to section manager.
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()

    def on_draw(self) -> None:
        self.clear()

    # def on_update(self, delta_time: float):
    #     print(delta_time)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                title_view = TitleView()
                title_view.title_y = WindowData.height * 0.75
                title_view.start_y = WindowData.height * 0.3
                self.window.show_view(title_view)

            case arcade.key.N:
                if eng.game_state.mission_board is not None:
                    eng.game_state.mission_board.clear_board()
                    eng.game_state.mission_board.fill_board(
                        max_enemies_per_room=3, room_amount=3
                    )

            case arcade.key.M:
                missions_view = MissionsView()
                self.window.show_view(missions_view)

            case arcade.key.R:
                roster_view = RosterView()
                self.window.show_view(roster_view)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height


class RosterView(arcade.View):
    state = ViewStates.ROSTER

    def __init__(self, window: Window = None):
        super().__init__(window)
        self.margin = 5
        self.merc = None
        self.color = arcade.color.WHITE

        # RosterAndTeamPane Config
        self.roster_and_team_pane_section = RosterAndTeamPaneSection(
            left=2,
            bottom=242,
            width=WindowData.width - 2,
            height=WindowData.height - 2,
            prevent_dispatch_view={False},
        )

        # RecruitmentPane Config
        self.recruitment_pane_section = RecruitmentPaneSection(
            name="recruitment_pane_section",
            left=2,
            bottom=242,
            width=WindowData.width - 2,
            height=WindowData.height - 2,
            prevent_dispatch_view={False},
        )

        # InfoPane Config
        self.instruction = UILabel(
            text=f"Assign members to the team before embarking on a mission!",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
            text_color=self.color,
        )
        self.entity_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
        )

        self.guild_funds = box_containing_horizontal_label_pair(
            (
                (" ", "right", 18, arcade.color.WHITE),
                (" ", "left", 18, arcade.color.GOLD),
            ),
            padding=(0, 0, 0, 50),
            size_hint=(1, None),
        )

        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, self.entity_info, self.guild_funds],
        )

        # CommandBar Config
        self.recruitment_pane_buttons = [
            self.roster_button(),
            nav_button(GuildView, "Guild"),
        ]
        self.roster_pane_buttons = [
            self.recruit_button(),
            nav_button(GuildView, "Guild"),
        ]
        self.command_bar_section = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.roster_pane_buttons,
            prevent_dispatch_view={False},
        )

        self.add_section(self.roster_and_team_pane_section)
        self.add_section(self.recruitment_pane_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def switch_to_recruitment_pane(self, event: UIEvent = None):
        """
        Do any necessary reconfiguration of recruitment_pane_section when switching to this section from the roster and team display.
        Ensures the section has appropriate window size values if the window was resized while recruitment section was disabled.
        Assigns the correct buttons to the command bar for this section.

        Attached to self.recruit_button as click_handler or called directly in on_key_press.
        """
        self.state = ViewStates.RECRUIT
        self.info_pane_section.manager.children[0][0].children[0].children[2].children[
            0
        ].label.text = "Guild Coffers: "
        self.info_pane_section.manager.children[0][0].children[0].children[2].children[
            1
        ].label.text = f"{eng.game_state.guild.funds} gp"
        # Disable the roster_and_team_pane_section
        self.roster_and_team_pane_section.enabled = False
        self.roster_and_team_pane_section.manager.disable()

        self.recruitment_pane_section.flush()
        self.recruitment_pane_section.manager.enable()
        self.recruitment_pane_section.enabled = True

        # Set up CommandBar with appropriate buttons
        self.command_bar_section.manager.disable()
        self.command_bar_section.buttons = self.recruitment_pane_buttons
        self.command_bar_section.flush()
        self.command_bar_section.manager.enable()

    def switch_to_roster_and_team_panes(self, event: UIEvent = None):
        """
        Do any necessary reconfiguration of roster_and_team_pane_section when switching to this section from the recruitment display.
        Ensures the section has appropriate window size values if the window was resized while roster_and_team_pane_section was disabled.
        Assigns the correct buttons to the command bar for this section.

        Attached to self.roster_button as click_handler and called directly in on_key_press.
        """
        self.state = ViewStates.ROSTER
        self.info_pane_section.manager.children[0][0].children[0].children[2].children[
            0
        ].label.text = ""
        self.info_pane_section.manager.children[0][0].children[0].children[2].children[
            1
        ].label.text = ""
        # Disable the recruitment_pane_section
        self.recruitment_pane_section.enabled = False

        # Flush and setup the section so that new recruits are present and selectable via the UIManager
        self.roster_and_team_pane_section.flush()
        self.roster_and_team_pane_section.enabled = True

        # Setup CommandBarSection with appropriate buttons
        self.command_bar_section.manager.disable()
        self.command_bar_section.buttons = self.roster_pane_buttons
        self.command_bar_section.flush()
        self.command_bar_section.manager.enable()

    def recruit_button(self) -> UIFlatButton:
        """Attached Handler will change from displaying the roster & team panes
        to showing recruits available for hire, with the appropriate command bar.

        Returns:
            UIFlatButton: Button with attached handler.
        """
        btn = UIFlatButton(
            text="Recruit "
        )  # Space at the end here to stop the t getting clipped when drawn.
        btn.on_click = self.switch_to_recruitment_pane
        return btn

    def roster_button(self) -> UIFlatButton:
        """Attached Handler will change from displaying the roster & team panes
        to showing recruits available for hire, with the appropriate command bar.

        Returns:
            UIFlatButton: Button with attached handler.
        """
        btn = UIFlatButton(text="Roster")
        btn.on_click = self.switch_to_roster_and_team_panes
        return btn

    def _roster_entity(self) -> None:
        """Sets self.merc to the selected entry in the roster scroll window.
        Allows the InfoPaneSection to display entity reference from RosterAndTeamPaneSection
        """
        if (
            self.roster_and_team_pane_section.pane_selector.pos == 0
            and len(self.roster_and_team_pane_section.roster_scroll_window.items) > 0
        ):
            self.merc = self.roster_and_team_pane_section.roster_scroll_window.items[
                self.roster_and_team_pane_section.roster_scroll_window.position.pos
            ]

    def _team_entity(self) -> None:
        """Sets self.merc to the selected entry in the team scroll window.
        Allows the InfoPaneSection to display entity reference from RosterAndTeamPaneSection
        """
        if (
            self.roster_and_team_pane_section.pane_selector.pos == 1
            and len(self.roster_and_team_pane_section.team_scroll_window.items) > 0
        ):
            self.merc = self.roster_and_team_pane_section.team_scroll_window.items[
                self.roster_and_team_pane_section.team_scroll_window.position.pos
            ]

    def _recruits_entity(self) -> None:
        """Sets self.merc to the selected entry in the recruitment scroll window.
        Allows the InfoPaneSection to display entity reference from RecruitmentPaneSection
        """
        if len(self.recruitment_pane_section.recruitment_scroll_window.items) > 0:
            self.merc = self.recruitment_pane_section.recruitment_scroll_window.items[
                self.recruitment_pane_section.recruitment_scroll_window.position.pos
            ]

    def on_show_view(self) -> None:
        self.info_pane_section.manager.enable()
        self.recruitment_pane_section.manager.enable()
        self.roster_and_team_pane_section.manager.enable()
        self.command_bar_section.manager.enable()

        self.recruitment_pane_section.enabled = False

    def on_hide_view(self) -> None:
        self.recruitment_pane_section.manager.disable()
        self.roster_and_team_pane_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.command_bar_section.manager.disable()

    def on_update(self, delta_time: float):
        self.merc = None
        if self.state == ViewStates.ROSTER:
            self._roster_entity()
            self._team_entity()

        if self.state == ViewStates.RECRUIT:
            self._recruits_entity()

        if self.merc is None:
            self.entity_info.text = ""
        else:
            self.entity_info.text = f"LVL: {self.merc.fighter.level}  |  HP: {self.merc.fighter.hp}  |  ATK: {self.merc.fighter.power}  |  DEF: {self.merc.fighter.defence}"

    def on_draw(self) -> None:
        self.clear()

    def _log_input(self, symbol, modifiers):
        ...

    def _log_state(self):
        ...

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self._log_input(symbol, modifiers)

        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.R:
                if self.state == ViewStates.ROSTER:
                    self.switch_to_recruitment_pane()

                elif self.state == ViewStates.RECRUIT:
                    self.switch_to_roster_and_team_panes()

        self._log_state()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        WindowData.width = width
        WindowData.height = height


class MissionsView(arcade.View):
    state = ViewStates.MISSIONS

    def __init__(self, window: Window = None):
        super().__init__(window)
        self.background = WindowData.mission_background
        self.margin = 5
        self.selection = Cycle(
            3, 2
        )  # 3 missions on screen, default selected (2) is the top visually.

        self.mission_section = MissionsSection(
            left=0,
            bottom=242,
            width=WindowData.width,
            height=WindowData.height - 242,
            prevent_dispatch_view={False},
            missions=eng.game_state.mission_board.missions,
        )

        # InfoPane config
        self.instruction = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
        )
        self.team_info = UILabel(
            text="",
            width=WindowData.width,
            font_size=18,
            font_name=WindowData.font,
            align="center",
            size_hint=(1, 1),
        )
        self.info_pane_section = InfoPaneSection(
            left=0,
            bottom=52,
            width=WindowData.width,
            height=188,
            prevent_dispatch_view={False},
            margin=self.margin,
            texts=[self.instruction, self.team_info],
        )

        # CommandBar Config
        self.buttons: list[UIFlatButton] = [nav_button(GuildView, "Guild")]
        self.command_bar_section: CommandBarSection = CommandBarSection(
            left=0,
            bottom=0,
            width=WindowData.width,
            height=50,
            buttons=self.buttons,
            prevent_dispatch_view={False},
        )
        self.add_section(self.mission_section)
        self.add_section(self.info_pane_section)
        self.add_section(self.command_bar_section)

    def on_show_view(self) -> None:
        self.mission_section.manager.enable()
        self.info_pane_section.manager.enable()
        self.command_bar_section.manager.enable()
        # Prepare text for display in InfoPaneSection.
        if len(eng.game_state.team.members) > 0:
            self.instruction.text = "Press Enter to Embark on a Mission!"
            self.team_info.text = (
                f"{len(eng.game_state.team.members)} Guild Members are ready to Embark!"
            )
            self.instruction.label.color = arcade.color.GOLD
            self.team_info.label.color = arcade.color.GOLD

        else:
            self.instruction.text = "No Guild Members are assigned to a team!"
            self.instruction.label.color = arcade.color.RED_DEVIL
            self.team_info.text = (
                "Assign Guild Members to a Team from the Roster before Embarking!"
            )
            self.team_info.label.color = arcade.color.RED_DEVIL

    def on_hide_view(self) -> None:
        """Disable the UIManager for this view.
        Ensures that a fresh UIManager can create buttons, assign handlers, and receive events
        from its own view after changing out of this view.
        """
        self.command_bar_section.manager.disable()
        self.info_pane_section.manager.disable()
        self.mission_section.manager.disable()

    def on_draw(self) -> None:
        self.clear()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                guild_view = GuildView()
                self.window.show_view(guild_view)

            case arcade.key.DOWN:
                self.selection.decr()

            case arcade.key.UP:
                self.selection.incr()

            case arcade.key.RETURN:
                eng.selected_mission = self.mission_section.mission_selection.pos
                eng.init_dungeon()
                if not eng.game_state.dungeon.cleared:
                    if len(eng.game_state.guild.team.members) > 0:
                        self.window.show_view(BattleView())


class BattleView(arcade.View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.combat_grid_section = CombatGridSection(
            left=0,
            bottom=WindowData.height / 2,
            width=WindowData.width,
            height=WindowData.height / 2,
            prevent_dispatch_view={False},
        )

        self.target_selection: Selection[tuple[Node, ...]] | None = None

        self.add_section(self.combat_grid_section)
        eng.init_combat()

    def on_show_view(self):
        eng.await_input()
        eng.combat_dispatcher.volatile_subscribe(
            "target_selection", "BattleView.set_input_request", self.set_input_request
        )

    def on_draw(self):
        self.clear()

    def set_input_request(self, event):
        print("set input request")
        selection = event["target_selection"]
        self.target_selection = Selection(selection["paths"])
        self.target_selection.set_confirmation(selection["confirmation_callback"])
        self.combat_grid_section.show_path(self.target_selection.current)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.G:
                if eng.mission_in_progress is False:
                    eng.flush_subscriptions()
                    guild_view = GuildView()
                    self.window.show_view(guild_view)

        if not self.target_selection:
            match symbol:
                case arcade.key.SPACE:
                    eng.next_combat_action()
                    eng.awaiting_input = False
            return

        match symbol:
            case arcade.key.UP:
                self.target_selection.prev()
                self.combat_grid_section.show_path(self.target_selection.current)
                print(self.target_selection)

            case arcade.key.DOWN:
                self.target_selection.next()
                self.combat_grid_section.show_path(self.target_selection.current)
                print(self.target_selection)

            case arcade.key.SPACE:
                ok = self.target_selection.confirm()
                if ok:
                    self.combat_grid_section.hide_path()
                    self.target_selection = None

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        WindowData.width = width
        WindowData.height = height

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        print(f"{self.combat_grid_section.grid_loc(Vec2(x,y))=}")
