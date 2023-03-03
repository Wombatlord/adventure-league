import unittest

from src.entities.entity import Entity, Name
from src.entities.fighter import Fighter


class TestFighter(unittest.TestCase):
    def test_attack(self):
        # Arrange
        f1 = Fighter(5, 1, 3, 1)
        f2 = Fighter(5, 1, 3, 1)

        en1 = Entity(
            Name("EN1"),
            0,
            fighter=f1,
        )

        en2 = Entity(Name("EN2"), 0, fighter=f2)

        # Action
        en1.fighter.attack(en2)
        en2.fighter.attack(en1)

        # Assert
        self.assertGreaterEqual(f1.max_hp, f1.hp)


if __name__ == "__main__":
    unittest.main()
