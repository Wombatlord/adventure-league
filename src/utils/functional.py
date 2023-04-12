from typing import Callable, Sequence


def call_in_order(callbacks: Sequence[Callable[[], None]]) -> Callable[[], None]:
    """
    Use this to compose callbacks to be called sequentially
    Args:
        callbacks: a collection of callbacks

    Returns: a function that when invoked, invokes the provided sequence of callbacks in the order provided

    """

    def _seq():
        for func in callbacks:
            func()

    return _seq
