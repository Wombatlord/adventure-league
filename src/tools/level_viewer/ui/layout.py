from __future__ import annotations

import random
from typing import Callable, Generator, Sequence

import arcade
from arcade.gl import geometry
from pyglet.math import Vec2

from src import config
from src.entities.sprites import BaseSprite
from src.gui.biome_textures import Biome, BiomeName, biome_map
from src.gui.combat.highlight import HighlightLayer
from src.textures.texture_data import SpriteSheetSpecs
from src.tools.level_viewer.model.layout import Block
from src.tools.level_viewer.ui.biome_menu import BiomeMenu
from src.tools.level_viewer.ui.geometry_menu import GeometryMenu
from src.tools.level_viewer.ui.hides import Hides
from src.utils.camera_controls import CameraController
from src.world.isometry.transforms import Transform
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace

NO_OP = lambda *_, **__: None


class SelectionCursor(int):
    pass


GREEN = SelectionCursor(0)
RED = SelectionCursor(2)
GOLD_EDGE = SelectionCursor(5)


class LayoutView(arcade.View):
    hiders: list[Hides]

    def __init__(self, parent_factory: Callable[[], arcade.View] | None = None):
        self.hiders = []
        super().__init__()
        window_dims = arcade.get_window().size
        self.parent_factory = parent_factory
        self.layout = LayoutSection(
            left=0, bottom=0, width=window_dims[0], height=window_dims[1]
        )
        self.geometry_menu = GeometryMenu(layout=self.layout)
        self.biome_menu = BiomeMenu(layout=self.layout)

        self.add_section(self.register_hider(self.geometry_menu))
        self.add_section(self.register_hider(self.biome_menu))
        self.add_section(self.layout)
        self.show_one(self.geometry_menu)

    def on_draw(self):
        self.clear()

    def register_hider(self, hider: arcade.Section | Hides) -> arcade.Section | Hides:
        self.hiders.append(hider)
        return hider

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.geometry_menu.on_resize(width, height)

    def toggle_ui(self, target: arcade.Section | Hides):
        for hider in self.hiders:
            if hider is target:
                hider.toggle()
            else:
                hider.hide()

    def show_one(self, menu: arcade.Section | Hides):
        for hider in self.hiders:
            if hider is menu:
                hider.show()
            else:
                hider.hide()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        {
            arcade.key.T: lambda: self.toggle_ui(self.geometry_menu),
            arcade.key.B: lambda: self.toggle_ui(self.biome_menu),
        }.get(symbol, NO_OP)()


class SurfaceBuffer:
    width: int
    height: int
    ctx: arcade.ArcadeContext

    def __init__(self, width: int, height: int, window: arcade.Window):
        self.width = width
        self.height = height
        self.quad_fs = geometry.quad_2d_fs()
        self.ctx = window.ctx
        self.texture = self.ctx.texture(
            (self.width, self.height),
            components=3,
            filter=(self.ctx.NEAREST, self.ctx.NEAREST)
        )
        self.display_program = self.ctx.program(
            vertex_shader="""
            #version 330
            
            in vec2 in_vert;
            in vec2 in_uv;
            out vec2 uv;

            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
                uv = in_uv;
            }
            """,
            fragment_shader="""
            #version 330

            uniform sampler2D texture0;
            out vec4 fragColor;
            in vec2 uv;

            void main() {

                fragColor = texture(texture0, uv);

            }
            """
        )



class LayoutSection(arcade.Section):
    TILE_BASE_DIMS = (16, 17)
    SET_ENCOUNTER_HANDLER_ID = "set_encounter"
    SPRITE_SCALE = 5

    layout: list[Block]
    pathing: PathingSpace | None

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(
            left, bottom, width, height, prevent_dispatch_view={False}, **kwargs
        )
        self._mouse_coords = Vec2(0, 0)

        self._original_dims = width, height

        self.world_sprite_list = arcade.SpriteList()
        self.grid_camera = arcade.Camera()
        self.grid_camera.zoom = 1.0
        self.cam_controls = CameraController(self.grid_camera)

        self.transform = Transform.isometric(
            block_dimensions=(16, 8, 8),
            absolute_scale=self.SPRITE_SCALE,
            translation=self.world_origin,
        )
        self.debug_text = ""
        self.last_mouse_node = Node(0, 0)

        self.layout = []
        self.pathing = None

        self._focus = Node(4, 4)
        self._last_clicked = Node(4, 4)
        self._follow = None
        self.highlight_layer_gold_edge = None
        self.highlight_layer_red = None
        self.highlight_layer_green = None
        self.setup_highlight_layers(self.world_sprite_list)
        self.follow(self.gen_last_clicked())
        self.current_biome = biome_map[random.choice(BiomeName.all_biomes())]

    def setup_highlight_layers(self, display: arcade.SpriteList):
        self.highlight_layer_gold_edge = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[GOLD_EDGE],
            offset=(0, 3.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
        ).attach_display(display)
        self.highlight_layer_green = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[GREEN],
            offset=(0, 4.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
        ).attach_display(display)
        self.highlight_layer_red = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[RED],
            offset=(0, 4.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
            draw_priority_bias=-0.01,
        ).attach_display(display)

    @property
    def world_origin(self) -> Vec2:
        return Vec2(self.width / 2, self.height / 4)

    def show_path(self, current: tuple[Node] | None) -> None:
        if not current:
            return

        self.show_highlight(
            green=current[:1],
            gold=current[1:-1],
            red=current[-1:],
        )

    def show_highlight(
        self,
        green: Sequence[Node] | None = None,
        gold: Sequence[Node] | None = None,
        red: Sequence[Node] | None = None,
    ):
        green = green or []
        gold = gold or []
        red = red or []

        self.highlight_layer_green.set_visible_nodes(green)
        self.highlight_layer_gold_edge.set_visible_nodes(gold)
        self.highlight_layer_red.set_visible_nodes(red)

        self.highlight_layer_green.show_visible()
        self.highlight_layer_gold_edge.show_visible()
        self.highlight_layer_red.show_visible()

        self.refresh_draw_order()

    def hide_path(self):
        self.clear_highlight()

    def clear_highlight(self):
        self.highlight_layer_green.hide_all()
        self.highlight_layer_gold_edge.hide_all()
        self.highlight_layer_red.hide_all()
        self.refresh_draw_order()

    def refresh_draw_order(self):
        self.world_sprite_list.sort(key=lambda s: s.get_draw_priority())

    def update_camera(self):
        self.cam_controls.on_update()
        self.update_focus()
        self.cam_controls.look_at_world(
            self.get_focus(), self.transform, distance_per_frame=0.2
        )
        self.grid_camera.update()

    def on_update(self, delta_time: float):
        self.update_camera()

    def on_draw(self):
        self.grid_camera.use()

        self.world_sprite_list.draw(pixelated=True)
        if config.DEBUG:
            l, r, b, t = self.grid_camera.projection
            arcade.draw_line(l, b, r, b, arcade.color.RED, line_width=4)
            arcade.draw_line(l, b, l, t, arcade.color.GREEN, line_width=4)

    def on_resize(self, width: int, height: int):
        self.width, self.height = width, height
        self.transform.on_resize(self.world_origin)
        self.grid_camera.resize(width, height)
        self.cam_controls.look_at_world(self.get_focus(), self.transform)
        for sprite in self.world_sprite_list:
            if isinstance(sprite, BaseSprite):
                sprite.update_position()

        self.on_update(0)

    def follow(self, node_gen: Generator[Node | None, None, None]):
        self._follow = node_gen

    def update_focus(self):
        if self._follow:
            self._focus = next(self._follow) or Node(4, 4)

    def get_focus(self) -> Node:
        return self._focus or Node(4, 4)

    def gen_last_clicked(self) -> Generator[Node | None, None, None]:
        while True:
            yield self._last_clicked

    def show_layout(self, layout: list[Block]) -> None:
        if not layout:
            return
        self.layout = [b.with_biome(self.current_biome) for b in layout]
        self.pathing = PathingSpace.from_nodes([b.node for b in layout])
        self.level_to_sprite_list()

        self.highlight_layer_red.set_space(self.pathing)
        self.highlight_layer_green.set_space(self.pathing)
        self.highlight_layer_gold_edge.set_space(self.pathing)

    def level_to_sprite_list(self):
        self.teardown_level()

        for block in self.layout:
            if not isinstance(block.texture, arcade.Texture):
                breakpoint()
            sprite = BaseSprite(
                block.texture,
                scale=self.SPRITE_SCALE,
                transform=self.transform,
            )
            sprite.set_node(block.node)
            self.world_sprite_list.append(sprite)

    def teardown_level(self):
        self.world_sprite_list.clear()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        node = self.node_at_mouse()
        if self.mouse_node_has_changed(node):
            self._last_clicked = node

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self._mouse_coords = Vec2(float(x), float(y))

    def node_at_mouse(self) -> Node:
        return self.transform.cast_ray(self.cam_controls.image_px(self._mouse_coords))

    def update_mouse_node(self, x: int, y: int, dx: int, dy: int) -> Node | None:
        self.on_mouse_motion(x, y, dx, dy)
        if not self.layout:
            return

        node = self.node_at_mouse()

        if not self.pathing.is_pathable(node):
            return

        if self.mouse_node_has_changed(node):
            self.set_mouse_node(node)
            return node

    def get_mouse_node(self) -> Node | None:
        return self.last_mouse_node

    def set_mouse_node(self, node: Node):
        self.last_mouse_node = node

    def mouse_node_has_changed(self, new_node: Node) -> bool:
        return self.last_mouse_node != new_node

    def on_key_press(self, symbol: int, modifiers: int):
        self.cam_controls.on_key_press(symbol)

    def on_key_release(self, _symbol: int, _modifiers: int):
        self.cam_controls.on_key_release(_symbol)

    def switch_biome(self, biome: Biome):
        self.current_biome = biome
        self.show_layout([b.with_biome(self.current_biome) for b in self.layout])
