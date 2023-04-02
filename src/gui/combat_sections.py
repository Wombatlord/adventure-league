import arcade
from pyglet.math import Vec2

from src import config
from src.engine.init_engine import eng
from src.entities.dungeon import Room
from src.entities.entity import Entity
from src.entities.sprites import BaseSprite
from src.gui.combat_screen import CombatScreen
from src.gui.selection_texture_enums import SelectionCursor
from src.gui.window_data import WindowData
from src.textures.texture_data import SpriteSheetSpecs
from src.utils.camera_controls import CameraController
from src.world.isometry.transforms import Transform
from src.world.node import Node


def do_nothing():
    pass


class CombatGridSection(arcade.Section):
    TILE_BASE_DIMS = (16, 17)
    SET_ENCOUNTER_HANDLER_ID = "set_encounter"
    SPRITE_SCALE = 5

    encounter_room: Room | None

    def __init__(
        self,
        left: int,
        bottom: int,
        width: int,
        height: int,
        **kwargs,
    ):
        super().__init__(left, bottom, width, height, **kwargs)

        self.encounter_room = None
        self._original_dims = width, height

        self.world_sprite_list = arcade.SpriteList()
        self.dudes_sprite_list = arcade.SpriteList()
        self.combat_screen = CombatScreen()
        self.grid_camera = arcade.Camera()
        self.grid_camera.zoom = 1.0
        self.other_camera = arcade.Camera()
        self._subscribe_to_events()
        self.cam_controls = CameraController(self.grid_camera)

        self.transform = Transform.isometric(
            block_dimensions=(16, 8, 8),
            absolute_scale=self.SPRITE_SCALE,
            translation=Vec2(self.width, self.height) / 2,
        )
        self.all_path_sprites = self.init_path()
        self.debug_text = ""

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

    def init_path(self) -> arcade.SpriteList:
        selected_path_sprites = arcade.SpriteList()
        start_sprite = BaseSprite(
            SpriteSheetSpecs.indicators.loaded[SelectionCursor.GREEN.value],
            scale=self.SPRITE_SCALE,
            transform=self.transform,
            draw_priority_offset=0.1,
        ).offset_anchor((0, 4.5))
        selected_path_sprites.append(start_sprite)

        main_path_tex = SpriteSheetSpecs.indicators.loaded[
            SelectionCursor.GOLD_EDGE.value
        ]
        for _ in range(1, 19):
            sprite = BaseSprite(
                main_path_tex,
                scale=self.SPRITE_SCALE,
                transform=self.transform,
                draw_priority_offset=0.1,
            ).offset_anchor((0, 3.5))

            selected_path_sprites.append(sprite)

        end_sprite = BaseSprite(
            SpriteSheetSpecs.indicators.loaded[SelectionCursor.RED.value],
            scale=self.SPRITE_SCALE,
            transform=self.transform,
            draw_priority_offset=0.1,
        ).offset_anchor((0, 4.5))

        selected_path_sprites.append(end_sprite)

        return selected_path_sprites

    def show_path(self, current: tuple[Node]):
        head = (0,)
        body = tuple(range(1, len(current) - 1))
        tail = (19,)
        rest = range(len(current) - 1, 19)

        visible = [*head, *body, *tail]
        invisible = rest

        for i, sprite in enumerate(self.all_path_sprites):
            if i in visible:
                node_idx = i if i in head + body else -1
                node = current[node_idx]
                sprite.set_node(node)
                if sprite not in self.world_sprite_list:
                    self.world_sprite_list.append(sprite)

            elif i in invisible:
                sprite.visible = True
                if sprite in self.world_sprite_list:
                    self.world_sprite_list.remove(sprite)

        self.refresh_draw_order()

    def hide_path(self):
        for sprite in self.all_path_sprites:
            if sprite in self.world_sprite_list:
                self.world_sprite_list.remove(sprite)

        self.refresh_draw_order()

    def refresh_draw_order(self):
        self.world_sprite_list.sort(key=lambda s: s.get_draw_priority())

    def on_update(self, delta_time: float):
        self.cam_controls.on_update()
        self.update_debug_text()
        eng.update_clock -= delta_time

        if not eng.awaiting_input:
            hook = eng.next_combat_event
        else:
            hook = do_nothing

        self.dudes_sprite_list.update_animation(delta_time=delta_time)

        if eng.update_clock < 0:
            # print(f"{self.__class__}.on_update: TICK")
            eng.reset_update_clock()
            hook()

    def update_debug_text(self):
        self.debug_text = "\n".join(
            [
                repr(self.cam_controls),
                self.view.input_mode.name,
            ]
        )

    def on_draw(self):
        self.grid_camera.use()

        self.world_sprite_list.draw(pixelated=True)

        self.other_camera.use()
        if config.DEBUG:
            arcade.Text(
                self.debug_text,
                10,
                WindowData.height - 20,
                multiline=True,
                width=self.width,
            ).draw()

        # if eng.awaiting_input:
        #     self.combat_screen.draw_turn_prompt()

        # if not eng.mission_in_progress:
        #     self.combat_screen.draw_turn_prompt()

        self.combat_screen.draw_message()
        self.combat_screen.draw_stats()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.grid_camera.set_viewport(
            (0, 0, width, height)
        )  # Stretch the sprites with the window resize
        self.other_camera.resize(
            viewport_width=width, viewport_height=height
        )  # Resize the camera displaying the combat text

    def set_encounter(self, event: dict) -> None:
        encounter_room = event.get("new_encounter", None)
        if encounter_room:
            self.encounter_room = encounter_room
            self.level_to_sprite_list()

            self.prepare_dude_sprites()
            self.update_dudes(event)

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
