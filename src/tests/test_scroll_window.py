import unittest
from src.gui.gui_utils import ScrollWindow

class ScrollWindowTest(unittest.TestCase):
    strings = ["foo", "bar", "baz", "buzz", "bez", "bezos"]

    def test_scroll_window_focuses_latest_addition_when_item_is_appended(self):
        # Arrange
        scroll = ScrollWindow(items=self.strings, visible_size=3)

        # Action
        scroll.append("musk")

        # Assert
        visible, selected = scroll.visible_items
        expected_visible, expected_selected = [*self.strings[-2:], "musk"], 2
        
        assert (
            visible == expected_visible
        ), f"The visible items were expected to be {expected_visible=}, received {visible=}"

        assert (
            selected == 2
        ), f"The selected item was expected to be {expected_selected=}, received {selected=}"

    def test_frame_is_dragged_on_successive_selection_increments(self):
        # Arrange
        scroll = ScrollWindow(items=self.strings, visible_size=3)

        # Action
        scroll.incr_selection()
        scroll.incr_selection()
        scroll.incr_selection()
        scroll.incr_selection()
        
        # Assert
        actual = scroll.visible_items
        expected = (self.strings[2:5], 2)

        assert (
            actual == expected
        ), f"The frame was not dragged as expected: {expected=}, {actual=}"

    def test_frame_is_dragged_on_successive_selection_decrements(self):
        # Arrange
        scroll = ScrollWindow(items=self.strings, visible_size=3)

        # Action
        scroll.decr_selection()
        scroll.decr_selection()
        scroll.decr_selection()
        scroll.decr_selection()
        
        # Assert
        actual = scroll.visible_items
        expected = (self.strings[2:5], 0)

        assert (
            actual == expected
        ), f"The frame was not dragged as expected: {expected=}, {actual=}"