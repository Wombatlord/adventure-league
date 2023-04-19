import hashlib
import unittest

from src.utils.proc_gen.constraints import check, load


class TestSyllables(unittest.TestCase):
    def test_syllable_check_finds_canary_string(self):
        # Arrange
        load()
        known_disallowed_string = "verbotenharam"

        # Action
        allowed = check(known_disallowed_string)

        # Assert
        assert not allowed

    def test_syllable_check_func_filters_disallowed_hash(self):
        # Arrange
        known_disallowed_string = "disallowedteststring"
        hash_list = [hashlib.sha256(known_disallowed_string.encode()).digest()]

        # Action
        checked = check("disallowed_test_string", disallowed_hashes=hash_list)

        # Assert
        assert checked is False
