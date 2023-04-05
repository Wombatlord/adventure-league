import arcade
from arcade.gui import (
    UIAnchorLayout,
    UIBoxLayout,
    UIFlatButton,
    UILabel,
    UIManager,
    UIWidget,
)

from src.engine.init_engine import eng
from src.gui.buttons import CommandBarMixin
from src.gui.gui_components import box_containing_horizontal_label_pair, single_box
from src.gui.observer import observe
from src.gui.ui_styles import ADVENTURE_STYLE
from src.textures.texture_data import SingleTextureSpecs


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
            # button.with_border(width=3, color=arcade.color.GOLD)

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
        self.panel = SingleTextureSpecs.panel_highlighted.loaded

        self.manager.add(
            single_box(
                bottom=self.bottom,
                height=self.height,
                children=[*self.texts, self.guild_funds_info()],
                padding=(10, 0, 0, 0),
                panel=self.panel,
            )
        )

    # Considering moving the potential info available to view in the InfoPane into here.
    # The only issue at the moment is that obviously with this set up as is, the self.guild_funds_info() is in every views InfoPane.
    # I tried creating a sort of mode switch to determine the children for the UIManager with a function to return the appropriate composite set.
    # Got quite close but it kept breaking the observer defined below.
    # The info would display but not update with state change until returning to recruitment section.
    def guild_funds_info(self) -> UIWidget:
        def set_funds_label_text(ui_label: UILabel, funds: int) -> None:
            ui_label.text = f"{funds} gp"

        funds_text_observer = observe(
            get_observed_state=lambda: eng.game_state.guild.funds,
            sync_widget=set_funds_label_text,
        )

        guild_funds = box_containing_horizontal_label_pair(
            (
                ("Guild Coffers: ", "right", 24, arcade.color.WHITE),
                (
                    f"{eng.game_state.guild.funds}",
                    "left",
                    24,
                    arcade.color.GOLD,
                    funds_text_observer,
                ),
            ),
            padding=(0, 0, 0, 150),
            size_hint=(1, None),
        )

        return guild_funds

    def flush(self):
        self.manager = UIManager()

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.width = width
