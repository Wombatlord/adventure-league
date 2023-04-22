from typing import Iterable

import arcade
from pyglet.math import Vec2

from src.entities.sprites import BaseSprite
from src.world.isometry.transforms import Transform
from src.world.level.room import Room
from src.world.node import Node


class HighlightLayer:
    """
    This is intended to be used to manage tile based selection indicators for the
    isometric view.

    Each distinct texture needs to be managed by its own layer
    """

    _sprite_list: arcade.SpriteList | None
    _texture: arcade.Texture
    _room: Room | None
    _scale: float
    _transform: Transform
    _sprite_refs: dict[Node, BaseSprite]
    _visible_nodes: set[Node]

    def __init__(
        self,
        texture: arcade.Texture,
        offset: Vec2 | tuple[float, float],
        scale: float,
        transform: Transform,
    ):
        self._sprite_list = None
        self._texture = texture
        self._sprite_offset = offset
        self._room = None
        self._scale = scale
        self._transform = transform
        self._sprite_refs = {}
        self._visible_nodes = set()

    def attach_display(self, sprite_list: arcade.SpriteList):
        """
        This should be invoked once in the lifecycle of a layer during setup
        """
        if self._sprite_list:
            raise ValueError("The display is already attached")
        self._sprite_list = sprite_list
        if self._room:
            self._setup_sprites()

    def set_room(self, room: Room):
        """
        Call this when the room layout changes
        """
        self._room = room
        if self._sprite_list:
            self._setup_sprites()
        self._visible_nodes = set()

    def _setup_sprites(self):
        """
        Does the bulk of the heavy lifting around setting up the various references etc.
        Implements a lazy approach to
        """
        if self._room is None:
            raise ValueError("Cannot setup sprites if no room has been supplied")

        if self._sprite_list is None:
            raise ValueError("Cannot setup sprites if there is no display list")

        to_check = {*self._sprite_refs.keys()}
        for node in self._room.space.all_included_nodes(exclude_dynamic=False):
            to_check.remove(node)
            if highlight := self._sprite_refs.get(node, self._build_tile()):
                if highlight in self._sprite_list:
                    continue

            self._include_in_display(highlight, node)

        self._prune_stale_refs(to_check)

    def _prune_stale_refs(self, to_check):
        """Cache invalidation and sync with sprite list on pathing space change"""
        for node in to_check:
            if (stale_sprite := self._sprite_refs[node]) in self._sprite_list:
                self._sprite_list.remove(stale_sprite)
                del self._sprite_refs[node]

    def _build_tile(self) -> BaseSprite:
        return BaseSprite(
            self._texture,
            scale=self._scale,
            transform=self._transform,
            draw_priority_offset=0.1,
        ).offset_anchor(tuple(self._sprite_offset))

    def _include_in_display(self, sprite: BaseSprite, node: Node):
        """Called on attaching this layer to the rendered isometric world sprite list"""
        self._sprite_refs[node] = sprite
        sprite.set_node(node)
        sprite.visible = False
        self._sprite_list.append(sprite)

    def set_visible_nodes(self, nodes: Iterable[Node]):
        """
        Use this to supply the collection of nodes that aught to be highlighted with the sprite texture
        managed by this layer, this will cause them to be shown. If the node isn't in the space, it will
        be ignored.
        """
        new_visible_nodes = {*nodes}

        to_hide = self._visible_nodes - new_visible_nodes
        for node in to_hide:
            if highlight := self._sprite_refs.get(node):
                highlight.visible = False

        self._visible_nodes = new_visible_nodes
        self.hide_all()
        self.show_visible()

    def show_visible(self):
        """Use this to show the highlights that aught to be visible"""
        for node in self._visible_nodes:
            if highlight := self._sprite_refs.get(node):
                highlight.visible = True

    def hide_all(self):
        """
        Use this to hide all highlights from this layer. This does does not clear the nodes that
        should be visible, so it can be undone with a call to show_visible
        """
        for highlight in self._sprite_refs.values():
            highlight.visible = False
