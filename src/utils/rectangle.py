import operator
from typing import Any, NamedTuple, Self, Tuple

from arcade.camera import FourFloatTuple, FourIntTuple
from pyglet.math import Vec2

Real = int | float
FourNumbers = tuple[Real, Real, Real, Real]


class Rectangle(NamedTuple):
    """
    This class essentially "extends" the arcade.FourFloatTuple as it is
    used by the arcade.SimpleCamera.viewport

    The idea is to bundle up a bunch of concepts that aren't made explicit
    in calculations using FourFloatTuples.

    The rectangle has named constructors (from_projection, from_viewport)
    specifically for use with the arcade cameras because the camera uses
    the type in two different ways, both to represent a rectangle.

    This class aims to unify the representation and provide a readable
    abstraction to work with 2d projection that doesn't pointlessly
    overcomplicate things with matrices when it doesn't even perform
    better!
    """

    l: float
    r: float
    b: float
    t: float

    @property
    def x(self) -> float:
        return self.l

    @property
    def y(self) -> float:
        return self.b

    @classmethod
    def from_projection(cls, *projection: FourFloatTuple) -> Self:
        if len(projection) != 4 or any(
            not isinstance(f, float | int) for f in projection
        ):
            raise TypeError(
                f"Rectangle.from_projection expects to be passed a "
                f"tuple[{Real}, {Real}, {Real}, {Real}], got {projection=}"
            )
        return cls(*projection)

    @classmethod
    def from_lbrt(cls, lbrt: FourNumbers) -> Self:
        """
        For when you want to construct from a representation of a rectangle of the form:
        rect = leftmost_x, bottommost_y, rightmost_x, topmost_y
        Args:
            lbrt: tuple(leftmost_x, bottommost_y, rightmost_x, topmost_y)

        Returns: Rectangle

        """
        l, b, r, t = lbrt
        return cls(l=l, r=r, b=b, t=t)

    @classmethod
    def from_xywh(cls, x: float, y: float, w: float, h: float) -> Self:
        """
        See above
        """
        return cls.from_lbrt((x, y, w + x, h + y))

    @classmethod
    def from_limits(cls, min_v: Vec2, max_v: Vec2) -> Self:
        """
        For when you want to construct from a representation of a rectangle in the form:
        min_v = Vec2(left_x, bottom_y)
        max_v = Vec2(right_x, top_y)
        Args:
            min_v: Vec2(left_x, bottom_y)
            max_v: Vec2(right_x, top_y)

        Returns: Rectangle

        """
        return cls.from_lbrt((min_v.x, min_v.y, max_v.x, max_v.y))

    @classmethod
    def from_lbwh(cls, lbwh: FourFloatTuple) -> Self:
        """
        For when you want to construct from a representation of a rectangle of the form:
        rect = leftmost_x, bottommost_y, width, height

        This is the way the viewport is laid out for an arcade.Camera

        Args:
            lbwh: leftmost_x, bottommost_y, width, height

        Returns: Rectangle

        """
        l, b, w, h = lbwh
        return cls.from_lbrt((l, b, l + w, b + h))

    @classmethod
    def from_viewport(cls, viewport: FourFloatTuple) -> Self:
        """
        Specifically for the use case:
        camera = arcade.Camera()
        rectangle = Rectangle.from_viewport(camera.viewport)

        Just an alias for Rectangle.from_lbwh for the avoidance of any doubt about which to use.
        Args:
            viewport: get this from the arcade.Camera instance

        Returns: Rectangle

        """
        return cls.from_lbwh(viewport)

    def as_viewport(self) -> FourIntTuple:
        """Returns a FourFloatTuple with the ordering: left, bottom, width, height"""
        return (int(self.l), int(self.b), int(self.w), int(self.h))

    def as_projection(self) -> FourFloatTuple:
        """Returns a FourFloatTuple with the ordering: left, right, bottom, top"""
        return self

    @property
    def w(self) -> float:
        """
        The width of the rectangle in the coordinates used to instantiate it.
        Returns: float
        """
        return self.r - self.l

    @property
    def h(self) -> float:
        """
        The height of the rectangle in the coordinates used to instantiate it.
        Returns: float
        """
        return self.t - self.b

    @property
    def min(self) -> Vec2:
        """
        The 'smallest' corner. This is the coordinates of the bottom-left corner
        if x increases to the right and y increases upwards.
        Returns: Vec2

        """
        return Vec2(self.l, self.b)

    @property
    def max(self) -> Vec2:
        """
        The 'biggest' corner. This is the coordinates of the top-right corner
        if x increases to the right and y increases upwards.
        Returns: Vec2

        """
        return Vec2(self.r, self.t)

    @property
    def dims(self) -> Vec2:
        """
        The dimensions (width, height) of the rectangle in the coordinates that were used to instantiate it.
        Returns: Vec2

        """
        return self.max - self.min

    @property
    def center(self) -> Vec2:
        """
        This vector is the coordinates of the unique point that is equidistant from every corner.
        The returned vector is in the coordinates that were used to instantiate the Rectangle
        Returns: Vec2

        """
        return (self.max + self.min) / 2

    @property
    def bottom_left(self) -> Vec2:
        """
        The position vector of the bottom left corner. Equivalent to Rect.min.
        """
        return self.min

    @property
    def corners(self) -> tuple[Vec2, Vec2, Vec2, Vec2]:
        """Returns the positions of the corners of the rectangle clockwise from the bottom left"""
        return (
            Vec2(self.l, self.b),
            Vec2(self.l, self.t),
            Vec2(self.r, self.t),
            Vec2(self.r, self.b),
        )

    def scale_isotropic(self, factor: float, fixed_point: Vec2) -> Self:
        """
        This function returns a rectangle that has rect.scale(s, p).dims == rect.dims * s
        where s is the scale factor and p is the center of the scaling i.e. if the rectangle's
        bottom left isn't at p, it appears to move.

        Always returns a new instance
        Args:
            factor: The ratio new_width/old_width
            fixed_point: The point in the defining coord system that is unchanged by the scaling

        Returns: Rectangle

        """
        min_t, max_t = (self.min - fixed_point) * factor, (
            self.max - fixed_point
        ) * factor
        return Rectangle.from_limits(min_t + fixed_point, max_t + fixed_point)

    def affine_coords(self, coords: Vec2) -> Vec2:
        """
        This interprets the coordinates received as being in the system used to instantiate this rectangle,
        and returns the same point in the coordinate system defined such that this rectangle would appear
        as a square of side length one with the origin at its bottom-left corner

        Args:
            coords: a point in the rectangle's defining coords

        Returns: Vec2

        """
        if any(d == 0 for d in self.dims):
            raise ValueError(
                f"Rectangles should be 2-dimensional, this one is a line {self.dims=}, {self=}"
            )
        return Vec2(*map(operator.truediv, coords - self.min, self.dims))

    def lerp(self, affine_coords: Vec2, translate: bool) -> Vec2:
        """
        This is the inverse of Rectangle.affine_coords and can be used to map one rectangle to another by doing
        ap1 = rect1.affine_coords(p1)
        p12 = rect2.lerp(ap1)

        This maps center to center when translate is false.

        When translate is true, the offsets of the rectangles will not be resolved so if rect1 and rect2 have no overlap,
        then if p1 starts inside rect1, then p12 cannot be inside rect2. This can be thought of as just the scaling
        component of the transformation.
        Args:
            affine_coords: coordinates where the 1x1 square will be scaled to the dimensions of this rectangle
            translate: When true, the 1x1 square at the origin will be mapped exactly to this rectangle, i.e. this
            function becomes exactly the inverse of Rectangle.affine_coords

        Returns: Vec2

        """
        disp = self.min if translate else Vec2()
        return Vec2(*map(operator.mul, affine_coords, self.dims)) + disp

    def translate(self, displacement: Vec2) -> Self:
        """
        This returns a rectangle the same dimensions as this one, with its corners displaced by the displacement vector.

        Always returns a new instance.
        Args:
            displacement: The amount by which to move all corners

        Returns: Rectangle

        """
        return self.from_limits(self.min + displacement, self.max + displacement)

    def __contains__(self, other):
        if isinstance(other, Rectangle):
            return (
                other.l >= self.l
                and other.r < self.r
                and other.b >= self.b
                and other.t < self.t
            )
        
        if isinstance(other, tuple | Vec2):
            return (
                self.l <= other[0] < self.r 
                and self.b <= other[1] < self.t
            )

        return False