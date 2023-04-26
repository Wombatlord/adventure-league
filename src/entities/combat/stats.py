class HealthPool:
    def __init__(self, max: int) -> None:
        self._max_hp = max
        self._current_hp = max
        self._bonus_hp = 0

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def current(self):
        return self._current_hp

    @current.setter
    def current(self, value):
        self._current_hp = value

    def decrease_bonus_hp(self, amount) -> int:
        if self._bonus_hp - amount < 0:
            breakthrough = self._bonus_hp - amount
            self._bonus_hp = 0
            return abs(breakthrough)

        else:
            self._bonus_hp -= amount
            return 0

    def decrease_current(self, amount: int):
        if self._bonus_hp > 0:
            breakthrough = self.decrease_bonus_hp(amount)
            self._current_hp -= breakthrough

        elif self._current_hp - amount < 0:
            self._current_hp = 0

        else:
            self._current_hp -= amount

    def increase_current(self, amount: int):
        if self._current_hp + amount > self._max_hp:
            self._current_hp = self._max_hp

        else:
            self._current_hp += amount


class FighterStats:
    defence: int
    power: int
    level: int
    max_range: int
    speed: int

    def __init__(self, defence, power, level, max_range, speed) -> None:
        self._defence = defence
        self._power = power
        self._level = level
        self._max_range = max_range
        self._speed = speed

    @property
    def defence(self):
        return self._defence

    @property
    def power(self):
        return self._power

    @property
    def level(self):
        return self._level

    @property
    def max_range(self):
        return self._max_range

    @property
    def speed(self):
        return self._speed
