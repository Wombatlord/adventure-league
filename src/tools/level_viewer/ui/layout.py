from __future__ import annotations

import math
import random
from typing import Callable, Generator, Sequence

import arcade
from pyglet.math import Vec2, Vec3

from src.config import DEBUG
from src.world.level.room_layouts import Z_INCR
from src.world.ray import Ray

DEBUG = True
from math import ceil

from src.entities.sprites import BaseSprite
from src.gui.biome_textures import Biome, BiomeName, biome_map
from src.gui.combat.highlight import HighlightLayer
from src.tests.utils.proc_gen.test_wave_function_collapse import HeightTile
from src.textures.texture_data import SpriteSheetSpecs
from src.tools.level_viewer.model.layout import Block
from src.tools.level_viewer.ui.biome_menu import BiomeMenu
from src.tools.level_viewer.ui.geometry_menu import GeometryMenu
from src.tools.level_viewer.ui.hides import Hides
from src.utils.camera_controls import CameraController
from src.utils.proc_gen.wave_function_collapse import (
    IrreconcilableStateError,
    from_distribution,
    generate,
)
from src.utils.proc_gen.wfc_tiling import rot
from src.world.isometry.transforms import Transform
from src.world.node import Node
from src.world.pathing.pathing_space import PathingSpace

arcade.SpriteList
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
        if DEBUG:
            self.debug_text.draw()

        self.grid_camera.use()
        self.world_sprite_list.draw(pixelated=True)

        if DEBUG:
            l, r, b, t = self.grid_camera.projection
            arcade.draw_line(l, b, r, b, arcade.color.RED, line_width=4)
            arcade.draw_line(l, b, l, t, arcade.color.GREEN, line_width=4)
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

    def height_map(self):
        dist = {HeightTile(i): 1 for i in range(3)}

        factory = from_distribution(dist)
        try:
            result = generate(factory)
        except IrreconcilableStateError:
            raise

        result = [*result.values()]

        return result

    def chunk_into_n(self, lst, n):
        size = ceil(len(lst) / n)
        return list(map(lambda x: lst[x * size : x * size + size], list(range(n))))

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

    def teardown_level(self):
        self.world_sprite_list.clear()

    def highlight_cursor(self, x: int, y: int):
        s: arcade.Sprite
        mouse = x, y
        click = self.cam_controls.image_px(
            Vec2(*mouse) if mouse else self._mouse_coords
        )
        for s in self.world_sprite_list[::-1]:
            if s.collides_with_point(click):
                self._last_clicked = s.node
                self.show_highlight(red=[self._last_clicked])
                self.debug_text.update("ray_hit", f"{self._last_clicked}")
                break

    def sample(self, x: int, y: int, button: int, modifiers: int):
        clicked_node = self.node_at_mouse((x, y))
        self.debug_text.update("clicked_node", f"{clicked_node}")

        if self._last_clicked != self.get_mouse_node():
            ray_hit = self.cast_click_ray(0.0)
            if not ray_hit:
                return
            self._last_clicked = ray_hit
            self.show_highlight(red=[self._last_clicked])
            self.debug_text.update("ray_hit", f"{ray_hit}")
            print(f"{self._last_clicked=}")

    def on_mouse_press(self, x, y, button, modifiers):
        self._is_clickin = True
        pass

    def on_mouse_release(self, *args):
        self._is_clickin = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self._mouse_coords = Vec2(float(x), float(y))

    def node_at_mouse(self, mouse: tuple[int, int] | None = None) -> Node:
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

    def cast_click_ray(self, z_offset=0) -> Node | None:
        world_click = self.node_at_mouse()
        projection_surface_coords = self.cam_controls.image_px(
            self._mouse_coords + self.offset_vec
        )
        toward_scene = self.transform.world_location(projection_surface_coords, z=-100)
        print(f"RAY FROM {world_click} to {toward_scene}")
        ray = Ray(start=world_click)

        surface = self.surface_geom()

        ray_z = world_click.z
        stop = ray.interpolate_z(look_at=toward_scene, z_stop=ray_z)
        snapped = lambda s: Node(round(s.x), round(s.y), s.z)

        ray_nodes = [None] * 8

        while (stop - world_click).mag < 50:
            if (ray_node := snapped(stop)) in surface:
                hit = ray_nodes[-1]
                print(f"HIT {hit=}")
                return hit
            ray_nodes = ([ray_node] + ray_nodes)[:2]
            print(f"CASTING {ray_node}")

            ray_z -= Z_INCR
            stop = ray.interpolate_z(look_at=toward_scene, z_stop=ray_z)

        print("MISSED")
        return None

        # for node in ray.cast(toward_scene):
        #     if (node - prev).z > 0:
        #         raise ValueError("We're sposed to be going down not up ding dong")
        #     print(f"RAY: {node=}")
        #     if node in self.geometry:
        #         return node
        #     if node.z < 1:
        #         return node

        #     if node.z < 0:
        #         return node.above

        #     if node.z < -1:
        #         return node.above.above
        # return world_click

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
