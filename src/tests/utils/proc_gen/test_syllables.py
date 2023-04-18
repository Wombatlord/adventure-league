import unittest

from src.utils.proc_gen.constraints import check


class TestSyllables(unittest.TestCase):
    def test_syllable_check_func_filters_disallowed_hash(self):
        # Arrange
        known_disallowed_string = "disallowed_test_string"

        # Action
        checked = check(known_disallowed_string)

        # Assert
        assert checked is False
