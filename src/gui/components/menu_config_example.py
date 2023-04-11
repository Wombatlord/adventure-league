from src.gui.components.menu import ExecutableMenuItem, SubMenu, MenuSchema


def invoke_action(*_) -> None:
    """
    Standin for a callback to invoke either with UIManager on_click or keyboard on_select
    """
    return None

action_button: ExecutableMenuItem = ("do a thing", invoke_action)
a_submenu: SubMenu = [
    ("Option A", invoke_action), 
    ("Option B", invoke_action), 
    ("Option C", invoke_action),
]

start_menu: MenuSchema = [
    ("Begin", invoke_action),
    ("Load Game", a_submenu),
    ("Options", [
        ("Callable", invoke_action)
    ]),
    ("Exit", invoke_action),
]

combat_menu = [
    ("Move", invoke_action),
    ("Use Item", [ 
        ("Health Potion", invoke_action),
        ("Different Potion", invoke_action),
        ("Third Potion", invoke_action),
    ]),
    ("Attack", [
        ("zag'kat bog", invoke_action),
        ("mim", invoke_action),
        ("poghat", invoke_action),
    ]),
    ("Cast", [
        ("zag'kat bog", invoke_action),
        ("mim", invoke_action),
        ("poghat", invoke_action),
    ]),
    ("End", invoke_action),
]