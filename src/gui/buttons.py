from typing import Callable

import arcade
from arcade import get_window
from arcade.gui import UIBoxLayout, UIManager
from arcade.gui.events import UIEvent
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.layout import UIAnchorLayout


class CommandBarMixin:
    """
    Provides some methods to be implemented in any View which should have a command bar.
    
    Implementations in a View should compose that View's buttons with attached handlers, labels, and styling
    ready to be added to the UIManager.
    
    If a View has an unchanging command bar, simply implement command bar.
    If a View can change the displayed command bar without changing views, extend this class with
    extra methods and implement them in the appropriate view.
    """
    window: arcade.Window

    @property
    def command_bar(self) -> list[UIFlatButton]:
        ...

    @property
    def roster_command_bar(self) -> list[UIFlatButton]:
        ...
        
    @property
    def recruit_command_bar(self) -> list[UIFlatButton]:
        ...


UIEventHandler = Callable[[UIEvent], None]

def nav_handler(target: type[arcade.View]) -> UIEventHandler:
    """An UIEventHandler which changes the View.

    Args:
        target (type[arcade.View]): The target View to switch to, received from the UIFlatButton this handler is attached to.

    Returns:
        UIEventHandler: An implementation of a handler for a UIEvent (eg. on_click, on_keypress etc.) 
    """
    def _handle(event: UIEvent):
        get_window().show_view(target())

    return _handle

def nav_button(target: type[arcade.View], text: str) -> UIFlatButton:
    """A generic button for changing to a different View.

    Args:
        target (type[arcade.View]): The target View to change to, passed to the click handler of the button.
        text (str): The text to render on the button, typically the name of the view that will be displayed on click.

    Returns:
        UIFlatButton: A button with a text label and an attached click handler.
    """
    btn = UIFlatButton(text=text)
    btn.on_click = nav_handler(target)

    return btn
    
def compose_command_bar(manager: UIManager, buttons: list[UIFlatButton]) -> UIAnchorLayout:
    """Attaches the root node of the layout to the provided manager.
    Buttons are attached to the UIBoxLayout, which is the child of the root node.

    Call in a Views on_show_view(), or in a method of the View which wants to change the rendered buttons without
    actually changing Views.
    
    Args:
        manager (UIManager): The UIManager of a View which wants to have a command bar.
        buttons (list[UIFlatButton]): An array of UIFlatButtons with their own handlers already attached.

    Returns:
        UIAnchorLayout: The root node of the command bar UI which contains a UIBoxLayout as its child, the children of the UIBoxLayout
                        are the actual buttons.
    """
    # if not isinstance(manager, UIManager):
    #     raise TypeError(f"Manager must be of type UIManager but you provided {type(manager)}")
    # if type(buttons) is not type(list[UIFlatButton]):
    #     raise TypeError(f"Buttons must be of type list[UIFlatButton] but you provided {type(buttons)}")
    
    anchor = manager.add(UIAnchorLayout())
    command_box = (
        UIBoxLayout(
            vertical=False,
            height = 30,
            children=buttons,
            size_hint=(1,None),
        )
        .with_padding()
    )

    anchor.add(
        anchor_x="center_x",
        anchor_y="bottom",
        child=command_box,
    )
    
    return anchor
