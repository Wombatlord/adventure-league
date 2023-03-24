import arcade
from arcade.texture import Texture

from src.engine.init_engine import eng
from src.world.pathing.grid_utils import Node, Space

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Sprite Sheet"

"""
PROTOTYPING SPRITE VIEWER UTILITY.
THIS SHOULD CURRENTLY BE RUN INDEPENDANT OF THE MAIN APPLICATION.
WILL CREATE ITS OWN WINDOW.
"""


entities = arcade.load_spritesheet(
    "assets/sprites/IsometricTRPGAssetPack_OutlinedEntities.png",
    sprite_width=16,
    sprite_height=16,
    columns=4,
    count=130,
    margin=1,
)

tiles = arcade.load_spritesheet(
    "assets/sprites/Isometric_MedievalFantasy_Tiles.png",
    sprite_height=17,
    sprite_width=16,
    columns=11,
    count=111,
    margin=0,
)

indicators = arcade.load_spritesheet(
    "assets/sprites/TRPGIsometricAssetPack_MapIndicators.png",
    sprite_height=8,
    sprite_width=16,
    columns=2,
    count=6,
    margin=0,
)


class EntitySprite(arcade.Sprite):
    def __init__(
        self,
        textures: list[Texture],
        tex_idx: int,
        win_dims: tuple[int, int],
        scale: int,
    ):
        super().__init__(scale=scale)

        self.textures = textures
        self.tex_idx = tex_idx
        self.texture = textures[tex_idx]
        self.center_x, self.center_y = win_dims[0] / 2, win_dims[1] / 2


class TileSprite(arcade.Sprite):
    def __init__(
        self,
        textures: list[Texture],
        tex_idx: int,
        win_dims: tuple[int, int],
        scale: int,
    ):
        super().__init__(scale=scale)

        self.textures = textures
        self.tex_idx = tex_idx
        self.texture = textures[tex_idx]
        self.center_x, self.center_y = win_dims[0] / 2, win_dims[1] / 2


class MyGame(arcade.Window):
    TILE_BASE_DIMS = (17, 16)
    SCALE_FACTOR = 0.2
    GRID_ASPECT = (2.35, 1.1)

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # self.grid_scale = 1
        self.constant_scale = self.TILE_BASE_DIMS[0] * self.SCALE_FACTOR * 5

        self.space = Space(Node(0, 0), Node(1, 1))
        self.space.exclusions.add(Node(1, 0))
        self.space.exclusions.add(Node(0, 1))

        self.iterable_entity_sprite = EntitySprite(entities, 0, self.get_size(), 6)
        self.iterable_tile_sprite = TileSprite(tiles, 0, self.get_size(), 6)
        self.entity_center_mark_sprite = EntitySprite(indicators, 0, self.get_size(), 1)
        self.tile_center_mark_sprite = EntitySprite(indicators, 0, self.get_size(), 1)
        self.sprite_list = arcade.SpriteList()

        self.left_pressed = False
        self.right_pressed = False
        self.a_pressed = False
        self.d_pressed = False
        self.entity_sheet_label = arcade.Text(
            text=f"Entity SpriteSheet Path: ./assets/sprites/IsometricTRPGAssetPack_OutlinedEntities.png",
            start_x=self.size[0] / 2,
            start_y=self.size[1] - 50,
            align="left",
            anchor_x="center",
        )

        self.tile_sheet_label = arcade.Text(
            text=f"Tiles SpriteSheet Path: ./assets/sprites/Isometric_MedievalFantasy_Tiles.png",
            start_x=self.size[0] / 2,
            start_y=self.size[1] - 100,
            align="left",
            anchor_x="center",
        )

        self.control_label = arcade.Text(
            text=f"WASD to cycle floor sprites. Arrow Keys to cycle entity sprites.",
            start_x=self.size[0] / 2,
            start_y=self.size[1] - 150,
            align="left",
            anchor_x="center",
        )

        self.control_label2 = arcade.Text(
            text=f"Green diamond overlaid on sprite centers, press Space to hide.",
            start_x=self.size[0] / 2,
            start_y=self.size[1] - 175,
            align="left",
            anchor_x="center",
        )

        self.anchor_label = arcade.Text(
            text=f"Anchor",
            start_x=self.iterable_entity_sprite.center_x - 200,
            start_y=self.iterable_entity_sprite.center_y,
            align="left",
            anchor_x="center",
        )

        self.actual_anchor_label = arcade.Text(
            text=f"",
            start_x=self.iterable_entity_sprite.center_x - 200,
            start_y=self.iterable_entity_sprite.center_y - 25,
            align="left",
            anchor_x="center",
        )

        self.anchor_offset_label = arcade.Text(
            text=f"Anchored Sprites",
            start_x=self.iterable_entity_sprite.center_x - 200,
            start_y=self.iterable_entity_sprite.center_y - 50,
            align="left",
            anchor_x="center",
        )

        self.sprite_anchors_label = arcade.Text(
            text="EntitySprite anchored to Node(1,1) Tile Sprite",
            start_x=self.iterable_entity_sprite.center_x - 200,
            start_y=self.iterable_entity_sprite.center_y - 75,
            align="left",
            anchor_x="center",
        )

        self.entity_idx_label_header = arcade.Text(
            text=f"Entity Sprite Index:",
            start_x=self.iterable_entity_sprite.center_x + 150,
            start_y=self.iterable_entity_sprite.center_y,
        )

        self.entity_idx_label = arcade.Text(
            text=f"{self.iterable_entity_sprite.tex_idx}",
            start_x=self.iterable_entity_sprite.center_x + 150,
            start_y=self.iterable_entity_sprite.center_y - 15,
        )

        self.tile_idx_label_header = arcade.Text(
            text=f"Tile Sprite Index:",
            start_x=self.iterable_entity_sprite.center_x + 150,
            start_y=self.iterable_entity_sprite.center_y - 80,
        )

        self.tile_idx_label = arcade.Text(
            text=f"{self.iterable_entity_sprite.tex_idx}",
            start_x=self.iterable_entity_sprite.center_x + 150,
            start_y=self.iterable_entity_sprite.center_y - 95,
        )

    def setup(self):
        # Set up the Floor Tiles
        w, h = self.get_size()

        for x in range(self.space.maxima.x, -1, -1):
            for y in range(self.space.maxima.y, -1, -1):
                offset = eng.grid_offset(
                    x, y, self.constant_scale, self.GRID_ASPECT, w, h / 2
                )
                iterable_tile_sprite = TileSprite(tiles, 0, self.get_size(), 5)
                iterable_tile_sprite.center_x = offset.x
                iterable_tile_sprite.center_y = offset.y
                self.sprite_list.append(iterable_tile_sprite)

        # Prepare a sprite for any Exclusion in the Space
        for ex in self.space.exclusions:
            ex_sprite = TileSprite(tiles, 43, self.get_size(), 5)
            offset = eng.grid_offset(
                ex.x + 1, ex.y + 1, self.constant_scale, self.GRID_ASPECT, w, h / 2
            )
            ex_sprite.center_x, ex_sprite.center_y = offset.x, offset.y
            self.sprite_list.append(ex_sprite)

        # Set the EntitySprite positioning
        self.iterable_entity_sprite.center_x, self.iterable_entity_sprite.center_y = (
            self.sprite_list[0].center_x,
            self.sprite_list[0].center_y,
        )

        (
            self.entity_center_mark_sprite.center_x,
            self.entity_center_mark_sprite.center_y,
        ) = (
            self.sprite_list[0].center_x,
            self.sprite_list[0].center_y,
        )

        # self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.bottom - self.iterable_tile_sprite.center_y}"

        self.tile_center_mark_sprite.center_x, self.tile_center_mark_sprite.center_y = (
            self.sprite_list[0].center_x,
            self.sprite_list[0].center_y,
        )

        # self.sprite_list.append(self.iterable_tile_sprite)
        self.sprite_list.append(self.iterable_entity_sprite)
        self.sprite_list.append(self.tile_center_mark_sprite)
        self.sprite_list.append(self.entity_center_mark_sprite)

    def on_draw(self):
        self.clear()
        self.entity_sheet_label.draw()
        self.tile_sheet_label.draw()
        self.control_label.draw()
        self.control_label2.draw()
        self.anchor_label.draw()
        self.actual_anchor_label.draw()
        self.anchor_offset_label.draw()
        self.sprite_anchors_label.draw()
        self.sprite_list.draw(pixelated=True)
        self.entity_idx_label_header.draw()
        self.entity_idx_label.draw()
        self.tile_idx_label_header.draw()
        self.tile_idx_label.draw()

    def on_update(self, delta_time: float):
        self.set_sprite_index_labels()
        self.constant_iterate_entity_sprites(self.iterable_entity_sprite)
        self.constant_iterate_tile_sprites(self.sprite_list[:4])

    def set_sprite_index_labels(self):
        if self.iterable_entity_sprite.tex_idx != self.entity_idx_label.text:
            if self.iterable_entity_sprite.tex_idx < 0:
                self.entity_idx_label.text = (
                    len(self.iterable_entity_sprite.textures)
                ) + self.iterable_entity_sprite.tex_idx

            else:
                self.entity_idx_label.text = self.iterable_entity_sprite.tex_idx

        if self.sprite_list[0].tex_idx != self.tile_idx_label.text:
            if self.sprite_list[0].tex_idx < 0:
                self.tile_idx_label.text = (
                    len(self.sprite_list[0].textures)
                ) + self.sprite_list[0].tex_idx

            else:
                self.tile_idx_label.text = self.sprite_list[0].tex_idx

    def constant_iterate_entity_sprites(self, sprite):
        match (self.right_pressed, self.left_pressed):
            case (True, False):
                self.incr_sprite_tex_index(sprite)

            case (False, True):
                self.decr_sprite_tex_index(sprite)

    def constant_iterate_tile_sprites(self, sprite):
        match (self.d_pressed, self.a_pressed):
            case (True, False):
                self.incr_sprite_tex_index(sprite)

            case (False, True):
                self.decr_sprite_tex_index(sprite)

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.SPACE:
                self.show_hide_center_markers()

            case arcade.key.ENTER:
                self.swap_anchor_between_center_and_bottom()

            case arcade.key.LEFT:
                self.left_pressed = True

            case arcade.key.RIGHT:
                self.right_pressed = True

            case arcade.key.D:
                self.d_pressed = True

            case arcade.key.A:
                self.a_pressed = True

            case arcade.key.UP:
                self.incr_sprite_tex_index(self.iterable_entity_sprite)

            case arcade.key.DOWN:
                self.decr_sprite_tex_index(self.iterable_entity_sprite)

            case arcade.key.W:
                self.incr_sprite_tex_index(self.sprite_list[:4])

            case arcade.key.S:
                self.decr_sprite_tex_index(self.sprite_list[:4])

    def swap_anchor_between_center_and_bottom(self):
        if self.iterable_entity_sprite.center_y != self.sprite_list[0].center_y:
            self.actual_anchor_label.text = f"Centers Overlapping"
            self.iterable_entity_sprite.center_y = self.sprite_list[0].center_y
            self.entity_center_mark_sprite.center_y = (
                self.tile_center_mark_sprite.center_y
            )

        else:
            self.actual_anchor_label.text = f"Tile.center_y = EntitySprite.bottom"
            self.iterable_entity_sprite.bottom = self.iterable_tile_sprite.center_y
            self.entity_center_mark_sprite.center_y = (
                self.iterable_entity_sprite.center_y
            )
            self.tile_center_mark_sprite.center_y = self.iterable_tile_sprite.center_y

    def show_hide_center_markers(self):
        if self.entity_center_mark_sprite.alpha > 0:
            self.entity_center_mark_sprite.alpha = 0
            self.tile_center_mark_sprite.alpha = 0

        else:
            self.entity_center_mark_sprite.alpha = 255
            self.tile_center_mark_sprite.alpha = 255

    def decr_sprite_tex_index(self, sprite: list[arcade.Sprite] | arcade.Sprite):
        if isinstance(sprite, list):
            for s in sprite:
                if abs(s.tex_idx) == len(s.textures):
                    s.tex_idx = 0
                    s.texture = s.textures[s.tex_idx]

                else:
                    s.tex_idx -= 1
                    s.texture = s.textures[s.tex_idx]

        else:
            if abs(sprite.tex_idx) == len(sprite.textures):
                sprite.tex_idx = 0
                sprite.texture = sprite.textures[sprite.tex_idx]

            else:
                sprite.tex_idx -= 1
                sprite.texture = sprite.textures[sprite.tex_idx]

    def incr_sprite_tex_index(self, sprite: list[arcade.Sprite] | arcade.Sprite):
        if isinstance(sprite, list):
            for s in sprite:
                if abs(s.tex_idx) == len(s.textures) - 1:
                    s.tex_idx = 0
                    s.texture = s.textures[s.tex_idx]

                else:
                    s.tex_idx += 1
                    s.texture = s.textures[s.tex_idx]

        else:
            if sprite.tex_idx == len(sprite.textures) - 1:
                sprite.tex_idx = 0
                sprite.texture = sprite.textures[sprite.tex_idx]

            else:
                sprite.tex_idx += 1
                sprite.texture = sprite.textures[sprite.tex_idx]

    def on_key_release(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.LEFT:
                self.left_pressed = False

            case arcade.key.RIGHT:
                self.right_pressed = False

            case arcade.key.D:
                self.d_pressed = False

            case arcade.key.A:
                self.a_pressed = False


def main():
    window = MyGame()
    window.setup()
    arcade.run()
