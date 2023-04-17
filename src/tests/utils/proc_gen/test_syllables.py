import unittest
import src.utils.proc_gen.syllables as monkey_patched
from src.utils.proc_gen.syllables import syllables
from src.tests.fixtures import SyllablePatches, bad_syllables_likely


class TestSyllables(unittest.TestCase):
    def test_disallowed_syllable_is_matched_and_rejected(self) -> None:
        word = syllables(syl_func=bad_syllables_likely)
        assert "disallow" not in word
    
    def test_syllable_recursion_recurses_and_returns_properly(self) -> None:
        with_printout = True   # Set to True to examine recursion stack.
        if with_printout:
            # Arrange
            monkey_patched.syllables = SyllablePatches.syllables_with_recursion_printout

            # Action
            word = syllables(syl_func=bad_syllables_likely)
            
            # Assert
            assert "disallow" not in word
        
        else:
            assert True