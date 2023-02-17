import arcade
from arcade.gui import UIManager
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

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
        **kwargs
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

    def compose_command_bar(self, manager: UIManager, buttons: list[UIFlatButton]) -> None:
        """
        Attaches the root node of the layout to the provided manager.
        Buttons are attached to the UIBoxLayout, which is the child of the root node.
        
        Args:
            manager (UIManager): The UIManager of a View which wants to have a command bar.
            buttons (list[UIFlatButton]): An array of UIFlatButtons with their own handlers already attached.
        """
        anchor = manager.add(UIAnchorLayout())
        command_box = (
            UIBoxLayout(
                vertical=False,
                height = self.height,
                children=buttons,
                size_hint=(1, None),
            )
            .with_padding()
        )

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
            button.size_hint=(1/len(buttons), 1)
            button.style=ADVENTURE_STYLE
            button.with_border(width=2, color=arcade.color.GOLDENROD)

        return buttons