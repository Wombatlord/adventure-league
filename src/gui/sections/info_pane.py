import arcade
from arcade.gui import UILabel, UIManager

from src.gui.components.layouts import single_box
from src.textures.texture_data import SingleTextureSpecs


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
                children=self.texts,
                padding=(10, 0, 0, 0),
                panel=self.panel,
            )
        )

    def flush(self):
        self.manager = UIManager()

    def on_draw(self):
        self.manager.draw()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.width = width
