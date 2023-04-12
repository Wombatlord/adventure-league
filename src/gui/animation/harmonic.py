import math

from pyglet.math import Vec2


def harmonic_motion(amplitude, period, theta, phase_shift=0, v_shift=0):
    x = amplitude * math.sin(period * theta) + phase_shift
    y = amplitude * math.sin(period * theta) + v_shift
    return Vec2(x, y)
