from typing import Callable

from src.world.node import Node

OnConfirm = Callable[[Node | None], None]
ValidateSelection = Callable[[Node], bool]
ShowTemplate = Callable[[Node], None]
ClearTemplates = Callable[[], None]
GetCurrent = Callable[[], Node]
EnableParentMenu = Callable[[], None]


class NodeSelection:
    _on_confirm: OnConfirm
    _validate_selection: ValidateSelection
    _clear_templates: ClearTemplates
    _get_current: GetCurrent
    _enable_parent_menu: EnableParentMenu
    _current: Node | None

    def __init__(
        self,
        on_confirm: OnConfirm,
        validate_selection: ValidateSelection,
        show_template: ShowTemplate,
        clear_templates: ClearTemplates,
        get_current: GetCurrent,
        enable_parent_menu: EnableParentMenu,
        keep_last_valid: bool = False,
    ) -> None:
        self._on_confirm = on_confirm
        self._validate_selection = validate_selection
        self._clear_templates = clear_templates
        self._get_current = get_current
        self._enable_parent_menu = enable_parent_menu
        self._show_template = show_template
        self._current = None

        # Controls whether an invalid current selection should clear any preexisting valid selection.
        self._keep_last_valid = keep_last_valid

    def enable(self):
        self._clear_templates()
        self.on_selection_changed()

    def disable(self):
        self._current = None
        self._clear_templates()
        self._enable_parent_menu()

    def on_selection_changed(self):
        self._current = self._get_current()

        if self._validate_selection(self._current):
            self._show_template(self._current)

        elif not self._keep_last_valid:
            self._current = None
            self._clear_templates()

    def on_selection_confirmed(self):
        if self._current is None:
            return

        if not self._validate_selection(self._current):
            self._clear_templates()
            return

        self._on_confirm(self._current)
        self._current = None
        self._clear_templates()
