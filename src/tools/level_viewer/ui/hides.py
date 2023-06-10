from __future__ import annotations

from typing import Callable

NO_OP = lambda *_, **__: None


class Hides:
    _draw_func: Callable[[], None] = NO_OP
    _hidden: bool = False

    @property
    def hidden(self) -> bool:
        return self._hidden

    def on_hide(self):
        pass

    def on_show(self):
        pass

    def hide(self):
        if self.hidden:
            return

        if hasattr(self, "on_draw"):
            self._draw_func = self.on_draw
            self.on_draw = NO_OP
        self.on_hide()
        self._hidden = True

    def show(self):
        if not self.hidden:
            return

        if hasattr(self, "on_draw"):
            self.on_draw = self._draw_func
            self._draw_func = NO_OP
        self.on_show()
        self._hidden = False

    def toggle(self):
        if self.hidden:
            self.show()
        else:
            self.hide()
