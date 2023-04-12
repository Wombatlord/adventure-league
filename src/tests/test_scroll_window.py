import unittest

from src.gui.components.scroll_window import ScrollWindow


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

    def test_selection_is_valid_when_selection_is_max_and_pop_is_called(self):
        # Arrange
        sc = ScrollWindow(self.strings, 3)

        sc.incr_selection()
        sc.incr_selection()
        sc.incr_selection()
        sc.incr_selection()
        sc.incr_selection()

        # Action
        sc.pop(-1)

        # Assert
        assert (
            sc.position.max == len(self.strings) - 2
        ), f"The position cycle length was not adjusted: {sc.position.max=} {len(sc.items)=}"

        assert (
            sc.position.pos == sc.position.max
        ), f"The position was not dragged by the pop: {sc.position.pos=}, {sc.position.max=}"

        assert (
            sc.frame_end == sc.position.max + 1
        ), f"The frame was not dragged to the selection: {sc.frame_end=} {sc.position.max=}"

    def test_selection_is_valid_when_selection_is_zero_and_pop_is_called_with_zero(
        self,
    ):
        # Arrange
        sc = ScrollWindow(self.strings, 3)

        # Action
        sc.pop(0)

        # Assert
        assert (
            sc.position.pos == 0
        ), f"The position should remain at zero: {sc.position.pos=}"

        assert (
            sc.frame_start == 0
        ), f"The frame_start should remain at zero: {sc.frame_start=}"

    def test_selection_hoists_tail_when_middle_element_is_popped(self):
        # Arrange
        sc = ScrollWindow(self.strings, 3)

        # Action
        sc.incr_selection()  # selection down one from top

        sc.pop(sc.position.pos)  # pop selection

        # Assert
        expected = (
            [
                *self.strings[:1],  # one element before the popped selection
                *self.strings[2:4],  # two elements after the popped selection
            ],
            1,  # The middle element is selected
        )
        assert (
            sc.visible_items == expected
        ), f"The visible items and selection should be {expected=}, we got {sc.visible_items=}"

    def test_selection_hoists_tail_when_penultimate_element_is_popped(self):
        # Arrange
        sc = ScrollWindow(self.strings, 3)

        # Action
        for _ in range(5):  # selection down five from top
            sc.incr_selection()
        sc.decr_selection()  # then back up one from bottom

        sc.pop(sc.position.pos)  # pop selection

        # Assert
        expected = (
            [
                *self.strings[-4:-2],  # the two elements before the popped item
                *self.strings[-1:],
            ],  # the final element
            2,  # if the tail is hoisted, our selection is now the final item
        )
        assert (
            sc.visible_items == expected
        ), f"The visible items and selection should be {expected=}, we got {sc.visible_items=}"
