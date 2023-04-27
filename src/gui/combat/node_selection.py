from typing import Callable

from src.world.node import Node

OnConfirm = Callable[[Node | None], None]
ValidateSelection = Callable[[Node], bool]
ShowTemplate = Callable[[Node], None]
ClearTemplates = Callable[[], None]
GetCurrent = Callable[[], Node]
EnableParentMenu = Callable[[], None]
OnEnter = Callable[[], None]
OnTeardown = Callable[[], None]


class NodeSelection:
    _on_confirm: OnConfirm
    _validate_selection: ValidateSelection
    _show_template: ShowTemplate
    _clear_templates: ClearTemplates
    _get_current: GetCurrent
    _on_enter: OnEnter
    _on_teardown: OnTeardown
    _enable_parent_menu: EnableParentMenu
    _current: Node | None
    _enabled: bool

    def __init__(
        self,
        on_confirm: OnConfirm,
        validate_selection: ValidateSelection,
        get_current: GetCurrent,
        show_template: ShowTemplate,
        clear_templates: ClearTemplates | None = None,
        on_enter: OnEnter | None = None,
        on_teardown: OnTeardown | None = None,
        keep_last_valid: bool = False,
    ) -> None:
        self._on_confirm = on_confirm
        self._validate_selection = validate_selection
        self._clear_templates = clear_templates or (lambda: None)
        self._get_current = get_current
        self._enable_parent_menu = None
        self._show_template = show_template
        self._current = None
        self._on_enter = on_enter or (lambda: None)
        self._on_teardown = on_teardown or (lambda: None)
        # Controls whether an invalid current selection should clear any preexisting valid selection.
        self._keep_last_valid = keep_last_valid
        self._enabled = False

    @property
    def enabled(self):
        return self._enabled

    def set_on_teardown(self, on_teardown: OnTeardown):
        self._on_teardown = on_teardown

    def set_on_enter(self, on_enter: OnEnter):
        self._on_enter = on_enter

    def set_clear_templates(self, clear_templates: ClearTemplates):
        self._clear_templates = clear_templates

    def set_enable_parent_menu(self, enable_parent_menu):
        self._enable_parent_menu = enable_parent_menu

    def enable(self):
        if self._enabled:
            return
        self._clear_templates()
        self.on_selection_changed()
        self._on_enter()
        self._enabled = True

    def disable(self):
        if not self._enabled:
            return
        self._current = None
        self._clear_templates()
        self._enable_parent_menu()
        self._enabled = False

    def on_selection_changed(self):
        if not self.enabled:
            return
        self._current = self._get_current()

        if self._validate_selection(self._current):
            self._show_template(self._current)

        elif not self._keep_last_valid:
            self._current = None
            self._clear_templates()

    def on_selection_confirmed(self):
        if not self.enabled:
            return

        if self._current is None:
            return

        if not self._validate_selection(self._current):
            self._clear_templates()
            return

        self._on_confirm(self._current)
        self._current = None
        self._clear_templates()
        self._on_teardown()
