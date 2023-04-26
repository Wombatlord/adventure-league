from typing import Callable

import arcade
from pyglet.math import Vec2

from src import config
from src.engine.init_engine import eng
from src.entities.entity import Entity
from src.entities.properties.locatable import Locatable
from src.entities.sprites import BaseSprite
from src.gui.combat.combat_components import CombatScreen
from src.gui.combat.highlight import HighlightLayer
from src.gui.components.menu import Menu
from src.textures.texture_data import SpriteSheetSpecs
from src.utils.camera_controls import CameraController
from src.world.isometry.transforms import Transform
from src.world.level.room import Room
from src.world.node import Node


def do_nothing():
    pass


class SelectionCursor:
    GREEN = 0
    YELLOW = 1
    RED = 2
    BLUE = 3
    SILVER_EDGE = 4
    GOLD_EDGE = 5


class Scene(arcade.Section):
    TILE_BASE_DIMS = (16, 17)
    SET_ENCOUNTER_HANDLER_ID = "set_encounter"
    SPRITE_SCALE = 5

    encounter_room: Room | None
    combat_menu: Menu | None

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

        self.encounter_room = None
        self._original_dims = width, height

        self.world_sprite_list = arcade.SpriteList()
        self.dudes_sprite_list = arcade.SpriteList()
        self.combat_screen = CombatScreen()
        self.grid_camera = arcade.Camera()
        self.grid_camera.zoom = 1.0
        self._subscribe_to_events()
        self.cam_controls = CameraController(self.grid_camera)

        self.transform = Transform.isometric(
            block_dimensions=(16, 8, 8),
            absolute_scale=self.SPRITE_SCALE,
            translation=self.world_origin,
        )
        self.debug_text = ""
        self.last_mouse_node = Node(0, 0)

        self._focus = Node(4, 4)
        self._follow = None

        # Selection Highlight Layers
        self.highlight_layer_gold_edge = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[SelectionCursor.GOLD_EDGE],
            offset=(0, 3.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
        ).attach_display(self.world_sprite_list)
        self.highlight_layer_green = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[SelectionCursor.GREEN],
            offset=(0, 4.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
        ).attach_display(self.world_sprite_list)
        self.highlight_layer_red = HighlightLayer(
            texture=SpriteSheetSpecs.indicators.loaded[SelectionCursor.RED],
            offset=(0, 4.5),
            scale=self.SPRITE_SCALE,
            transform=self.transform,
        ).attach_display(self.world_sprite_list)

    def _subscribe_to_events(self):
        eng.combat_dispatcher.volatile_subscribe(
            topic="new_encounter",
            handler_id="CombatGrid.set_encounter",
            handler=self.set_encounter,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="move",
            handler_id="CombatGrid.update_dudes",
            handler=self.update_dudes,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="cleanup",
            handler_id="CombatGrid.teardown_level",
            handler=self.teardown_level,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="attack",
            handler_id="CombatGrid.swap_textures_for_attack",
            handler=self.idle_or_attack,
        )

        eng.combat_dispatcher.volatile_subscribe(
            topic="dying",
            handler_id="CombatGrid.clear_dead_sprites",
            handler=self.clear_dead_sprites,
        )
        eng.combat_dispatcher.volatile_subscribe(
            topic="retreat",
            handler_id="CombatGrid.clear_retreating_sprites",
            handler=self.clear_retreating_sprites,
        )

    @property
    def world_origin(self) -> Vec2:
        return Vec2(self.width / 2, self.height / 4)

    def show_path(self, current: tuple[Node] | None) -> None:
        breakpoint()
        if not current:
            return

        self.show_highlight(
            green=current[:1],
            gold=current[1:-1],
            red=current[-1:],
        )

    def show_spell_template(self, template: list[Node]):
        self.show_highlight(red=template)

    def show_highlight(
        self,
        green: list[Node] | None = None,
        gold: list[Node] | None = None,
        red: list[Node] | None = None,
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
        eng.update_clock -= delta_time

        if not eng.awaiting_input:
            hook = eng.next_combat_event
        else:
            hook = do_nothing

        self.dudes_sprite_list.update_animation(delta_time=delta_time)

        if eng.update_clock < 0:
            eng.reset_update_clock()
            hook()
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

    def follow(self, locatable: Locatable):
        self._follow = locatable

    def update_focus(self):
        self._focus = self._follow.location if self._follow else None

    def get_focus(self) -> Node:
        return self._focus or Node(4, 4)

    def set_encounter(self, event: dict) -> None:
        encounter_room = event.get("new_encounter", None)
        if encounter_room:
            self.encounter_room = encounter_room
            self.level_to_sprite_list()
            self.prepare_dude_sprites()
            self.update_dudes(event)

        self.highlight_layer_red.set_room(self.encounter_room)
        self.highlight_layer_green.set_room(self.encounter_room)
        self.highlight_layer_gold_edge.set_room(self.encounter_room)

    def level_to_sprite_list(self):
        self.world_sprite_list.clear()
        for node in self.encounter_room.layout:
            sprite = BaseSprite(
                SpriteSheetSpecs.tiles.loaded[89],
                scale=self.SPRITE_SCALE,
                transform=self.transform,
            )
            sprite.set_node(node)
            self.world_sprite_list.append(sprite)

    def prepare_dude_sprites(self):
        """
        Constructs the sprite list with the appropriate sprites when starting a dungeon.
        Clears the sprite when entering a new room and reconstructs with new room member sprites.
        """
        if not self.dudes_sprite_list:
            self.dudes_sprite_list = arcade.SpriteList()
        else:
            self.dudes_sprite_list.clear()

        for dude in self.encounter_room.occupants:
            if dude.fighter.is_boss:
                dude.entity_sprite.sprite.scale = dude.entity_sprite.sprite.scale * 1.5
            dude.entity_sprite.sprite.set_transform(self.transform)
            dude.entity_sprite.sprite.set_node(dude.locatable.location)

            dude.entity_sprite.orient(dude.locatable.orientation)
            self.world_sprite_list.append(dude.entity_sprite.sprite)
            self.dudes_sprite_list.append(dude.entity_sprite.sprite)

    def update_dudes(self, _: dict) -> None:
        self._update_dudes()

    def _update_dudes(self):
        """
        Check if any sprites associated to a dead entity are still in the list, if so remove them.
        Iterate over the occupants of the current room and update the positional information of their sprites as
        necessary. Sort the sprite list such that sprites higher in screen space are drawn first and then overlapped
        by lower sprites.
        """
        if self.encounter_room is None:
            return

        for dude in self.encounter_room.occupants:
            dude.entity_sprite.sprite.set_node(dude.locatable.location)
            dude.entity_sprite.orient(dude.locatable.orientation)

        self.refresh_draw_order()

    def teardown_level(self):
        self.dudes_sprite_list.clear()
        self.world_sprite_list.clear()

    def idle_or_attack(self, event):
        dude = event["attack"]
        dude.entity_sprite.swap_idle_and_attack_textures()

    def clear_retreating_sprites(self, event):
        retreating_dude = event.get("dying") or event.get("retreat")
        retreating_dude.owner.entity_sprite.sprite.remove_from_sprite_lists()

    def clear_dead_sprites(self, event):
        """
        If a sprite is associated to a dead entity, remove the sprite from the sprite list.
        """
        dead_dude: Entity = event.get("dying") or event.get("retreat")
        dead_dude.entity_sprite.sprite.remove_from_sprite_lists()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self._mouse_coords = Vec2(float(x), float(y))

    def update_mouse_node(self, x: int, y: int, dx: int, dy: int) -> Node | None:
        self.on_mouse_motion(x, y, dx, dy)
        if not self.encounter_room:
            return

        node = self.transform.cast_ray(self.cam_controls.image_px(self._mouse_coords))

        if node not in self.encounter_room.space:
            return

        if self.mouse_node_has_changed(node):
            self.set_mouse_node(node)
            return Node

    def get_mouse_node(self) -> Node | None:
        return self.last_mouse_node

    def set_mouse_node(self, node: Node):
        self.last_mouse_node = node

    def mouse_node_has_changed(self, new_node: Node) -> bool:
        return self.last_mouse_node != new_node
