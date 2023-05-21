from typing import Generator, NamedTuple, Self, Callable

from pyglet.math import Mat4, Vec2, Vec3, Vec4

from src.utils.rectangle import Rectangle, Corner


class GridLoc(NamedTuple):
    x: int
    y: int

    @classmethod
    def snap(cls, v: Vec2) -> Self:
        return cls(x=round(v[0]), y=round(v[1]))

    def as_vec2(self) -> Vec2:
        return Vec2(*self)


class SnapGrid:
    _pin: Callable[[], Vec2] | None
    _corner: Corner | None

    def __init__(self, slot_size: Vec2, screen_area: Rectangle) -> None:
        self.bounds = screen_area
        self.slot_size = slot_size
        self._to_slot_offset = Mat4.from_scale(Vec3(*slot_size, 1))
        self._to_grid_transform = ~self._to_slot_offset
        self._pin, self._corner = None, None

    @classmethod
    def from_grid_dimensions(
        cls, w: int, h: int, slot_size: Vec2, bottom_left: Vec2
    ) -> Self:
        on_screen_dims = Vec2(
            x=w * slot_size.x,
            y=h * slot_size.y,
        )

        screen_area = Rectangle.from_limits(
            min_v=bottom_left, max_v=bottom_left + on_screen_dims
        )

        return cls(slot_size, screen_area)
    
    def pin_corner(self, corner: Corner,  pin: Callable[[], Vec2]):
        self._pin = pin
        self._corner = corner

    def on_resize(self):
        if not self._corner or not self._pin:
            return
        
        self.bounds = self.bounds.with_corner_at(self._corner, self._pin())

    def translation(self) -> Vec2:
        return self.bounds.min + self.slot_size * 0.5

    def to_screen(self, grid_loc: Vec2) -> Vec2:
        slot_offset = Vec2(*(self._to_slot_offset @ Vec4(*grid_loc, 0, 0))[:2])
        screen_pos = slot_offset + self.translation()
        return screen_pos

    def to_grid(self, screen_pos: Vec2) -> Vec2:
        slot_offset = screen_pos - self.translation()
        grid_space_vec = Vec2(*(self._to_grid_transform @ Vec4(*slot_offset, 0, 0))[:2])
        return grid_space_vec

    def to_grid_loc(self, screen_pos: Vec2) -> GridLoc:
        grid_pos = self.to_grid(screen_pos)
        return GridLoc.snap(grid_pos)

    def snap_to_grid(self, screen_pos: Vec2) -> Vec2 | None:
        if not self.in_screen_area(screen_pos):
            return

        grid_vec = self.to_grid(screen_pos)
        snapped = GridLoc.snap(grid_vec)

        return self.to_screen(snapped.as_vec2())

    @property
    def grid_bounds(self) -> Rectangle:
        return Rectangle.from_limits(
            min_v=self.to_grid(self.bounds.min),
            max_v=self.to_grid(self.bounds.max),
        )

    def in_grid(self, grid_loc: GridLoc) -> bool:
        return grid_loc.as_vec2() in self.grid_bounds

    def in_screen_area(self, screen_loc: Vec2):
        return screen_loc in self.bounds

    def locations_in_rows(self) -> Generator[Vec2, None, None]:
        top_left = GridLoc.snap(Vec2(0, self.grid_bounds.t - 0.5))
        along = lambda gl: GridLoc(gl.x + 1, gl.y)
        next_row = lambda gl: GridLoc(0, gl.y - 1)

        loc = top_left
        while self.in_grid(loc):
            while self.in_grid(loc):
                yield self.to_screen(loc.as_vec2())

                loc = along(loc)
            loc = next_row(loc)
