import arcade

from arcade.texture import Texture

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Sprite Sheet"

"""
PROTOTYPING SPRITE VIEWER UTILITY.
THIS SHOULD CURRENTLY BE RUN INDEPENDANT OF THE MAIN APPLICATION.
WILL CREATE ITS OWN WINDOW.
"""


entities = arcade.load_spritesheet(
    "C:\\Users\\Owner\\Code\\PythonProjects\\adventure_league\\assets\\sprites\\IsometricTRPGAssetPack_OutlinedEntities.png",
    sprite_width=16,
    sprite_height=16,
    columns=4,
    count=130,
    margin=1,
)

tiles = arcade.load_spritesheet(
    "C:\\Users\\Owner\\Code\\PythonProjects\\adventure_league\\assets\\sprites\\Isometric_MedievalFantasy_Tiles.png",
    sprite_height=17,
    sprite_width=16,
    columns=11,
    count=111,
    margin=0,
)

indicators = arcade.load_spritesheet(
    "C:\\Users\\Owner\\Code\\PythonProjects\\adventure_league\\assets\\sprites\\TRPGIsometricAssetPack_MapIndicators.png",
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
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.iterable_entity_sprite = EntitySprite(entities, 0, self.get_size(), 6)
        self.iterable_tile_sprite = TileSprite(tiles, 0, self.get_size(), 6)
        self.entity_center_mark_sprite = EntitySprite(indicators, 0, self.get_size(), 1)
        self.tile_center_mark_sprite = EntitySprite(indicators, 0, self.get_size(), 1)
        self.y_offset = 15
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
            start_x=self.iterable_entity_sprite.center_x - 175,
            start_y=self.iterable_entity_sprite.center_y,
            align="left",
            anchor_x="center",
        )

        self.actual_anchor_label = arcade.Text(
            text=f"",
            start_x=self.iterable_entity_sprite.center_x - 175,
            start_y=self.iterable_entity_sprite.center_y - 25,
            align="left",
            anchor_x="center",
        )

        self.anchor_offset_label = arcade.Text(
            text=f"Anchor Offset",
            start_x=self.iterable_entity_sprite.center_x - 175,
            start_y=self.iterable_entity_sprite.center_y - 50,
            align="left",
            anchor_x="center",
        )
        
        self.actual_anchor_offset_label = arcade.Text(
            text="",
            start_x=self.iterable_entity_sprite.center_x - 175,
            start_y=self.iterable_entity_sprite.center_y - 75,
            align="left",
            anchor_x="center",
        )

        self.entity_idx_label_header = arcade.Text(
            text=f"Index:",
            start_x=self.iterable_entity_sprite.center_x + 50,
            start_y=self.iterable_entity_sprite.center_y,
        )

        self.entity_idx_label = arcade.Text(
            text=f"{self.iterable_entity_sprite.tex_idx}",
            start_x=self.iterable_entity_sprite.center_x + 50,
            start_y=self.iterable_entity_sprite.center_y - 15,
        )

        self.tile_idx_label_header = arcade.Text(
            text=f"Index:",
            start_x=self.iterable_tile_sprite.center_x + 50,
            start_y=self.iterable_tile_sprite.center_y - 80,
        )

        self.tile_idx_label = arcade.Text(
            text=f"{self.iterable_tile_sprite.tex_idx}",
            start_x=self.iterable_tile_sprite.center_x + 50,
            start_y=self.iterable_tile_sprite.center_y - 95,
        )

    def setup(self):
        self.iterable_tile_sprite.center_y = self.iterable_entity_sprite.bottom - self.y_offset
        
        self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.bottom - self.iterable_tile_sprite.center_y}"
        
        self.tile_center_mark_sprite.center_x, self.tile_center_mark_sprite.center_y = (
            self.iterable_tile_sprite.center_x,
            self.iterable_tile_sprite.center_y,
        )

        self.sprite_list.append(self.iterable_tile_sprite)
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
        self.actual_anchor_offset_label.draw()
        self.sprite_list.draw(pixelated=True)
        self.entity_idx_label_header.draw()
        self.entity_idx_label.draw()
        self.tile_idx_label_header.draw()
        self.tile_idx_label.draw()

    def on_update(self, delta_time: float):
        self.set_sprite_index_labels()
        self.constant_iterate_entity_sprites()
        self.constant_iterate_tile_sprites()

    def set_sprite_index_labels(self):
        if self.iterable_entity_sprite.tex_idx != self.entity_idx_label.text:
            if self.iterable_entity_sprite.tex_idx < 0:
                self.entity_idx_label.text = (
                    len(self.iterable_entity_sprite.textures)
                ) + self.iterable_entity_sprite.tex_idx

            else:
                self.entity_idx_label.text = self.iterable_entity_sprite.tex_idx

        if self.iterable_tile_sprite.tex_idx != self.tile_idx_label.text:
            if self.iterable_tile_sprite.tex_idx < 0:
                self.tile_idx_label.text = (
                    len(self.iterable_tile_sprite.textures)
                ) + self.iterable_tile_sprite.tex_idx

            else:
                self.tile_idx_label.text = self.iterable_tile_sprite.tex_idx

    def constant_iterate_entity_sprites(self):
        match (self.right_pressed, self.left_pressed):
            case (True, False):
                if (
                    self.iterable_entity_sprite.tex_idx
                    == len(self.iterable_entity_sprite.textures) - 1
                ):
                    self.iterable_entity_sprite.tex_idx = 0
                    self.iterable_entity_sprite.texture = (
                        self.iterable_entity_sprite.textures[
                            self.iterable_entity_sprite.tex_idx
                        ]
                    )

                else:
                    self.iterable_entity_sprite.tex_idx += 1
                    self.iterable_entity_sprite.texture = (
                        self.iterable_entity_sprite.textures[
                            self.iterable_entity_sprite.tex_idx
                        ]
                    )

            case (False, True):
                if (
                    self.iterable_entity_sprite.tex_idx
                    < -len(self.iterable_entity_sprite.textures) + 1
                ):
                    self.iterable_entity_sprite.tex_idx = 0
                    self.iterable_entity_sprite.texture = (
                        self.iterable_entity_sprite.textures[
                            self.iterable_entity_sprite.tex_idx
                        ]
                    )

                else:
                    self.iterable_entity_sprite.tex_idx -= 1
                    self.iterable_entity_sprite.texture = (
                        self.iterable_entity_sprite.textures[
                            self.iterable_entity_sprite.tex_idx
                        ]
                    )

    def constant_iterate_tile_sprites(self):
        match (self.d_pressed, self.a_pressed):
            case (True, False):
                if (
                    self.iterable_tile_sprite.tex_idx
                    == len(self.iterable_tile_sprite.textures) - 1
                ):
                    self.iterable_tile_sprite.tex_idx = 0
                    self.iterable_tile_sprite.texture = (
                        self.iterable_tile_sprite.textures[
                            self.iterable_tile_sprite.tex_idx
                        ]
                    )

                else:
                    self.iterable_tile_sprite.tex_idx += 1
                    self.iterable_tile_sprite.texture = (
                        self.iterable_tile_sprite.textures[
                            self.iterable_tile_sprite.tex_idx
                        ]
                    )

            case (False, True):
                if (
                    self.iterable_tile_sprite.tex_idx
                    < -len(self.iterable_tile_sprite.textures) + 1
                ):
                    self.iterable_tile_sprite.tex_idx = 0
                    self.iterable_tile_sprite.texture = (
                        self.iterable_tile_sprite.textures[
                            self.iterable_tile_sprite.tex_idx
                        ]
                    )

                else:
                    self.iterable_tile_sprite.tex_idx -= 1
                    self.iterable_tile_sprite.texture = (
                        self.iterable_tile_sprite.textures[
                            self.iterable_tile_sprite.tex_idx
                        ]
                    )

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.SPACE:
                self.show_hide_center_markers()

            case arcade.key.ENTER:
                self.swap_anchor_between_center_and_bottom(self.y_offset)

            case arcade.key.LEFT:
                self.left_pressed = True

            case arcade.key.RIGHT:
                self.right_pressed = True

            case arcade.key.D:
                self.d_pressed = True

            case arcade.key.A:
                self.a_pressed = True

            case arcade.key.UP:
                if modifiers & arcade.key.MOD_SHIFT:
                    self.y_offset += 1
                    self.iterable_entity_sprite.bottom += self.y_offset
                    self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.bottom - self.iterable_tile_sprite.center_y}"
                
                else:
                    self.increment_entity_sprite_index()

            case arcade.key.DOWN:
                if modifiers & arcade.key.MOD_SHIFT:
                    self.y_offset -= 1
                    self.iterable_entity_sprite.bottom -= self.y_offset
                    self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.bottom - self.iterable_tile_sprite.center_y}"
                
                else:
                    self.decrement_entity_sprite_index()

            case arcade.key.W:
                self.increment_tile_sprite_index()

            case arcade.key.S:
                self.decrement_tile_sprite_index()

    def swap_anchor_between_center_and_bottom(self, y_offset):
        if (
                    self.iterable_entity_sprite.center_y
                    != self.iterable_tile_sprite.center_y
                ):
            self.actual_anchor_label.text = f"Centers Overlapping"
            self.iterable_entity_sprite.center_y = (
                        self.iterable_tile_sprite.center_y
                    )
            self.entity_center_mark_sprite.center_y = (
                        self.tile_center_mark_sprite.center_y
                    )
            self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.center_y - self.iterable_tile_sprite.center_y}"
        else:
            self.actual_anchor_label.text = (
                        f"Tile.center_y = EntitySprite.bottom"
                    )
            self.iterable_entity_sprite.bottom = (
                        self.iterable_tile_sprite.center_y + y_offset
                    )
            self.entity_center_mark_sprite.center_y = (
                        self.iterable_entity_sprite.center_y
                    )
            self.tile_center_mark_sprite.center_y = (
                        self.iterable_tile_sprite.center_y
                    )
            self.actual_anchor_offset_label.text = f"{self.iterable_entity_sprite.bottom - self.iterable_tile_sprite.center_y}"

    def show_hide_center_markers(self):
        if self.entity_center_mark_sprite.alpha > 0:
            self.entity_center_mark_sprite.alpha = 0
            self.tile_center_mark_sprite.alpha = 0

        else:
            self.entity_center_mark_sprite.alpha = 255
            self.tile_center_mark_sprite.alpha = 255

    def decrement_tile_sprite_index(self):
        if (
            self.iterable_tile_sprite.tex_idx
            == len(self.iterable_tile_sprite.textures) + 1
        ):
            self.iterable_tile_sprite.tex_idx = 0
            self.iterable_tile_sprite.texture = self.iterable_tile_sprite.textures[
                self.iterable_tile_sprite.tex_idx
            ]

        else:
            self.iterable_tile_sprite.tex_idx -= 1
            self.iterable_tile_sprite.texture = self.iterable_tile_sprite.textures[
                self.iterable_tile_sprite.tex_idx
            ]

    def increment_tile_sprite_index(self):
        if (
            self.iterable_tile_sprite.tex_idx
            == len(self.iterable_tile_sprite.textures) - 1
        ):
            self.iterable_tile_sprite.tex_idx = 0
            self.iterable_tile_sprite.texture = self.iterable_tile_sprite.textures[
                self.iterable_tile_sprite.tex_idx
            ]

        else:
            self.iterable_tile_sprite.tex_idx += 1
            self.iterable_tile_sprite.texture = self.iterable_tile_sprite.textures[
                self.iterable_tile_sprite.tex_idx
            ]

    def decrement_entity_sprite_index(self):
        if (
            self.iterable_entity_sprite.tex_idx
            < -len(self.iterable_entity_sprite.textures) + 1
        ):
            self.iterable_entity_sprite.tex_idx = 0
            self.iterable_entity_sprite.texture = self.iterable_entity_sprite.textures[
                self.iterable_entity_sprite.tex_idx
            ]

        else:
            self.iterable_entity_sprite.tex_idx -= 1
            self.iterable_entity_sprite.texture = self.iterable_entity_sprite.textures[
                self.iterable_entity_sprite.tex_idx
            ]

    def increment_entity_sprite_index(self):
        if (
            self.iterable_entity_sprite.tex_idx
            == len(self.iterable_entity_sprite.textures) - 1
        ):
            self.iterable_entity_sprite.tex_idx = 0
            self.iterable_entity_sprite.texture = self.iterable_entity_sprite.textures[
                self.iterable_entity_sprite.tex_idx
            ]

        else:
            self.iterable_entity_sprite.tex_idx += 1
            self.iterable_entity_sprite.texture = self.iterable_entity_sprite.textures[
                self.iterable_entity_sprite.tex_idx
            ]

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


if __name__ == "__main__":
    main()
