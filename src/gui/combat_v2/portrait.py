# import arcade
# from arcade import Camera
# from arcade.gl import Framebuffer, Texture2D
# from pyglet.math import Vec2
#
# from src.entities.entity import Entity
# from src.utils.rectangle import Rectangle
#
#
# class Portrait:
#     _rect: Rectangle
#     _entity: Entity | None
#     _sprite: arcade.Sprite | None
#     _visible: bool
#     _target_visibility: bool | None
#     _camera: arcade.Camera
#
#     @property
#     def _hidden_position(self) -> Vec2:
#         return self._sprite_region.center + Vec2(self._sprite.width, 0) * 2
#
#     @property
#     def _visible_position(self) -> Vec2:
#         return self._sprite_region.center
#
#     def __init__(self, portrait_rect: Rectangle, sprite_region: Rectangle):
#         self._rect = portrait_rect
#         self._visible = False
#         self._sprite = None
#         self._camera = arcade.Camera(viewport=portrait_rect, projection=sprite_region)
#         self._sprite_region = sprite_region
#         self._target_visibility = None
#         self._camera.center(self._hidden_position, speed=1)
#
#     def _sprite_is_visible(self) -> bool:
#         camera_offset = self._camera.position - self._sprite_region
#         return camera_offset.mag < self._sprite.width
#
#     def hide(self):
#         if self._target_visibility is False:
#             return
#         self._target_visibility = False
#         self._camera.center(self._hidden_position, speed=0.2)
#
#     def show(self):
#         if self._target_visibility is True:
#             return
#         self._target_visibility = True
#         self._camera.center(self._visible_position, speed=0.2)
#
#     def update(self):
#         if self._entity is None:
#             self.hide()
#
#         self._camera.update()
#
#         match self._camera.moving, self._target_visibility:
#             case False, True:
#                 self._visible = True
#                 self._target_visibility = None
#             case False, False:
#                 self._visible = False
#                 self._target_visibility = None
#                 if self._entity is not None and self._sprite is None:
#                     self._sprite = arcade.Sprite(self._entity.entity_sprite.sprite.texture
#             case _:
#                 pass
#
#
