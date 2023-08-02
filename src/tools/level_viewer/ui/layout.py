from __future__ import annotations

import math
import random
import time
from typing import Callable, Generator, Sequence

import arcade
from arcade.gl import geometry
from pyglet.math import Vec2

from src import config
from src.entities.sprites import BaseSprite
from src.gui.biome_textures import Biome, BiomeName, biome_map
from src.gui.combat.highlight import HighlightLayer
from src.textures.texture_data import SpriteSheetSpecs
from src.tools.level_viewer.model.viewer_state import Block
from src.tools.level_viewer.ui.biome_menu import BiomeMenu
from src.tools.level_viewer.ui.geometry_menu import GeometryMenu
from src.tools.level_viewer.ui.hides import Hides
from src.utils.camera_controls import CameraController
from src.utils.shader_program import Shader
from src.world.isometry.transforms import Transform
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace

NO_OP = lambda *_, **__: None


class SelectionCursor(int):
    pass


GREEN = SelectionCursor(0)
RED = SelectionCursor(2)
GOLD_EDGE = SelectionCursor(5)


class DebugText:
    def __init__(self):
        self.entries = {}
        self.text = arcade.Text(
            text="",
            start_x=200,
            start_y=arcade.get_window().height * 0.75,
            color=arcade.color.WHITE,
            font_size=18,
            multiline=True,
            width=800,
        )

    def update(self, id_: str, text: str | None = None):
        if text is None:
            return
        self.entries[id_] = text

        self.text.text = ""
        for k, v in self.entries.items():
            self.text.text += f"{k} = {v}\n"

        self.text.x = arcade.get_window().width * 0.1

    def draw(self):
        self.text.draw()


class LayoutView(arcade.View):
    hiders: list[Hides]
    pathing: PathingSpace

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
        self.debug_text = DebugText()

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
            hider.on_update(1 / 60)

    def show_one(self, menu: arcade.Section | Hides):
        for hider in self.hiders:
            if hider is menu:
                hider.show()
            else:
                hider.hide()

            hider.on_update(1 / 60)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        {
            arcade.key.T: lambda: self.toggle_ui(self.geometry_menu),
            arcade.key.B: lambda: self.toggle_ui(self.biome_menu),
        }.get(symbol, NO_OP)()


class NormalShader:
    width: int
    height: int
    ctx: arcade.ArcadeContext
    terrain_nodes: list[Node]

    def __init__(self, width: int, height: int, window: arcade.Window):
        self.width = width
        self.height = height
        self.ctx = window.ctx
        self.time = time.time()

        # render surface
        self.quad_fs = geometry.quad_2d_fs()

        # set up normal map texture/framebuffer pair
        self.normal_tex = self.ctx.texture(
            (self.width, self.height),
            components=4,
            filter=(self.ctx.NEAREST, self.ctx.NEAREST),
            dtype="f4",
        )
        self.normal_framebuffer = self.ctx.framebuffer(
            color_attachments=[self.normal_tex]
        )

        # set up scene map texture/framebuffer pair
        self.scene_tex = self.ctx.texture(
            (self.width, self.height),
            components=4,
            filter=(self.ctx.NEAREST, self.ctx.NEAREST),
            dtype="f4",
        )
        self.scene_framebuffer = self.ctx.framebuffer(
            color_attachments=[self.scene_tex]
        )
        self.shader = Shader(ctx=self.ctx)
        self.shader.load_sources(
            "./assets/shaders/disco/frag.glsl",
            "./assets/shaders/disco/vert.glsl",
        )
        self.shader.bind(self.normal_tex, "norm")
        self.shader.bind(self.scene_tex, "scene")
        self.shader.attach_uniform("time", self.get_time)

        self.normal_biome = biome_map[BiomeName.NORMALS]
        self.terrain_nodes = []
        self.normal_sprites = arcade.SpriteList()
        self.mouse = (0.0, 0.0)

    def get_time(self) -> float:
        return time.time() - self.time

    def update_terrain_nodes(self, sprites: arcade.SpriteList):
        self.normal_sprites.clear()
        for sprite in sprites:
            if not hasattr(sprite, "clone") or not getattr(sprite, "node", None):
                continue
            clone = sprite.clone()
            clone.texture = self.normal_biome.choose_texture_for_node(clone.node, 0)
            self.normal_sprites.append(clone)

    def update_mouse(self, v: Vec2):
        self.mouse = tuple([v.x / self.width, v.y / self.height])

    def render_scene(self, sprite_list: arcade.SpriteList):
        self.scene_framebuffer.clear()
        self.scene_framebuffer.use()
        sprite_list.draw(pixelated=True)

        self.normal_framebuffer.clear()
        self.normal_framebuffer.use()
        self.normal_sprites.draw(pixelated=True)

        self.ctx.screen.use()
        with self.shader as program:
            self.quad_fs.render(program)


class LayoutSection(arcade.Section):
    TILE_BASE_DIMS = (16, 17)
    SET_ENCOUNTER_HANDLER_ID = "set_encounter"
    SPRITE_SCALE = 5

    transform: Transform

    layout: list[Block]
    pathing: PathingSpace | None
    geometry_dims = (10, 10)
    geometry: list[Node]

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
        self._canvas_coords = Vec2(0, 0)

        self._original_dims = width, height

        self.world_sprite_list = arcade.SpriteList()
        self.grid_camera = arcade.Camera()
        self.grid_camera.zoom = 1.0
        self.cam_controls = CameraController(self.grid_camera)
        self.debug_cam = arcade.Camera()
        self.offset_vec = Vec2(0, 0)

        self.transform = Transform.isometric(
            block_dimensions=(16, 8, 8),
            absolute_scale=self.SPRITE_SCALE,
            translation=Vec2(0, 0),
        )
        print(self.transform.camera_z_axis())
        self.debug_text = DebugText()
        self.last_mouse_node = Node(0, 0)

        self.layout = []
        self.pathing = None
        self.geometry = []

        self._is_clickin = False

        self._focus = Node(4, 4)
        self._last_clicked = Node(4, 4)
        self._follow = None
        self.highlight_layer_gold_edge = None
        self.highlight_layer_red = None
        self.highlight_layer_green = None
        self.setup_highlight_layers(self.world_sprite_list)
        self.current_biome = biome_map[random.choice(BiomeName.all_biomes())]
        self.normal_shader = NormalShader(self.width, self.height, arcade.get_window())

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
            draw_priority_bias=-10,
        ).attach_display(display)

    def update_dims(self, x: int, y: int) -> None:
        self.geometry_dims = x, y

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

    def geom_by_height(self, z: float) -> list[Node]:
        return [n for n in self.geometry if n.z == z]

    def hide_path(self):
        self.clear_highlight()

    def clear_highlight(self):
        self.highlight_layer_green.hide_all()
        self.highlight_layer_gold_edge.hide_all()
        self.highlight_layer_red.hide_all()
        self.refresh_draw_order()

    def refresh_draw_order(self):
        self.world_sprite_list.sort(key=lambda s: self.transform.draw_priority(s.node))

    def update_camera(self):
        self.cam_controls.on_update()
        if focus := self.get_focus():
            self.cam_controls.look_at_world(
                focus, self.transform, distance_per_frame=0.05
            )

        self.grid_camera.update()

    def on_update(self, delta_time: float):
        self.update_camera()
        self.update_debug_text()
        self.highlight_cursor(*self._mouse_coords)

    def update_debug_text(self):
        self.debug_text.update("offset vec", f"{self.offset_vec}")

    def on_draw(self):
        self.grid_camera.use()
        self.normal_shader.render_scene(self.world_sprite_list)

        if config.DEBUG:
            l, r, b, t = self.grid_camera.projection
            arcade.draw_line(l, b, r, b, arcade.color.RED, line_width=4)
            arcade.draw_line(l, b, l, t, arcade.color.GREEN, line_width=4)
            arcade.draw_point(
                self._canvas_coords.x, self._canvas_coords.y, arcade.color.RED, 30
            )
            for s in self.world_sprite_list:
                s: arcade.Sprite
                s.draw_hit_box(arcade.color.WHITE)
                break

        self.debug_cam.use()

    def on_resize(self, width: int, height: int):
        self.width, self.height = width, height
        self.transform.on_resize(self.world_origin)
        self.grid_camera.resize(width, height)

        self.cam_controls.look_at_world(self.get_focus() or Node(4, 4), self.transform)
        for sprite in self.world_sprite_list:
            if isinstance(sprite, BaseSprite):
                sprite.update_position()

        self.on_update(0)

    def follow(self, node_gen: Generator[Node | None, None, None]):
        self._follow = node_gen

    def get_focus(self) -> Node:
        if self._is_clickin:
            return self._last_clicked

    def show_layout(self, layout: list[Block]) -> None:
        if not layout:
            return
        self.layout = [b.with_biome(self.current_biome) for b in layout]
        self.pathing = PathingSpace.from_nodes([b.node for b in layout])
        self.level_to_sprite_list()

        nodes = [block.node.above for block in self.layout]

        self.geometry = sorted(
            [block.node for block in self.layout], key=lambda n: -n.z
        )

        self.highlight_layer_red.set_nodes(nodes)
        self.highlight_layer_green.set_nodes(nodes)
        self.highlight_layer_gold_edge.set_nodes(nodes)

    def level_to_sprite_list(self):
        self.teardown_level()
        for block in self.layout:
            sprite = BaseSprite(
                block.texture,
                scale=self.SPRITE_SCALE,
                transform=self.transform,
            )
            sprite.set_node(block.node)
            self.world_sprite_list.append(sprite)
        self.refresh_draw_order()
        self.normal_shader.update_terrain_nodes(self.world_sprite_list)

    def teardown_level(self):
        self.world_sprite_list.clear()

    def highlight_cursor(self, x: int, y: int):
        s: arcade.Sprite
        mouse = x, y
        click = self.cam_controls.image_px(
            Vec2(*mouse) if mouse else self._mouse_coords
        )
        self._canvas_coords = click
        for s in self.world_sprite_list[::-1]:
            if s.collides_with_point(click):
                self._last_clicked = s.node
                self.show_highlight(red=[self._last_clicked])
                self.debug_text.update("ray_hit", f"{self._last_clicked}")
                break

    def on_mouse_press(self, x, y, button, modifiers):
        self._is_clickin = True
        pass

    def on_mouse_release(self, *args):
        self._is_clickin = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self._mouse_coords = Vec2(float(x), float(y))
        self.normal_shader.update_mouse(self._mouse_coords)

    def node_at_mouse(self, mouse: tuple[int, int] | None = None) -> Node:
        for s in self.world_sprite_list[::-1]:
            if s.collides_with_point(mouse):
                self._last_clicked = s.node
                self.show_highlight(red=[self._last_clicked])
                self.debug_text.update("ray_hit", f"{self._last_clicked}")
                return s.node
        projection_surface_coords = self.cam_controls.image_px(
            Vec2(*mouse) if mouse else self._mouse_coords
        )
        world_click = self.transform.world_location(projection_surface_coords, 100)
        return world_click

    def column_of(self, node: Node) -> list[Node]:
        return sorted(
            [b.node for b in self.layout if b.node[:2] == node[:2]], key=lambda n: -n.z
        )

    def surface_geom(self) -> list[Node]:
        return [b.node + Node(0, 0, 0.5) for b in self.layout]

    def update_mouse_node(self, x: int, y: int, dx: int, dy: int) -> Node | None:
        if not self.layout:
            return

        node = self.node_at_mouse()

        if self.mouse_node_has_changed(node):
            self.set_mouse_node(node)
            return node

    def get_mouse_node(self) -> Node | None:
        return self.last_mouse_node

    def set_mouse_node(self, node: Node):
        self.last_mouse_node = node

    def mouse_node_has_changed(self, new_node: Node) -> bool:
        return self.last_mouse_node != new_node

    def update_scene(self):
        for tile in self.world_sprite_list:
            if not hasattr(tile, "update_position"):
                continue
            tile.update_position()
        self.refresh_draw_order()

    def translate_level(self, translation: Node):
        self.transform.translate_grid(translation)
        self.update_scene()

    def rotate_level(self):
        if not self.layout:
            return
        self.transform.rotate_grid(
            math.pi / 2,
            (Vec2(*self.pathing.maxima[:2]) - Vec2(*self.pathing.minima[:2])) / 2,
        )
        self.update_scene()
        self.debug_text.update("screen origin", f"{self.transform.camera_origin()}")

    def on_key_press(self, symbol: int, modifiers: int):
        print(symbol)
        self.cam_controls.on_key_press(symbol)
        if symbol == arcade.key.L:
            breakpoint()
        n = Node(0, 0)
        {
            arcade.key.UP: lambda: self.translate_level(n.north),
            arcade.key.RIGHT: lambda: self.translate_level(n.east),
            arcade.key.DOWN: lambda: self.translate_level(n.south),
            arcade.key.LEFT: lambda: self.translate_level(n.west),
            arcade.key.R: lambda: self.rotate_level(),
            arcade.key.X: lambda: self.incr_offset_vec(Vec2(1, 0)),
            arcade.key.C: lambda: self.incr_offset_vec(Vec2(-1, 0)),
            arcade.key.Y: lambda: self.incr_offset_vec(Vec2(0, 1)),
            arcade.key.U: lambda: self.incr_offset_vec(Vec2(0, -1)),
        }.get(symbol, NO_OP)()

    def incr_offset_vec(self, by: Vec2):
        self.offset_vec += by

    def on_key_release(self, _symbol: int, _modifiers: int):
        self.cam_controls.on_key_release(_symbol)

    def switch_biome(self, biome: Biome):
        self.current_biome = biome
        self.show_layout([b.with_biome(self.current_biome) for b in self.layout])
