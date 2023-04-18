import functools
import random
import string
from typing import Callable

from src.utils.proc_gen.constraints import check


def inoffensive(logging=True, check_func=lambda: True):
    def decorator(gen_func) -> Callable[[], str]:
        @functools.wraps(gen_func)
        def _inoffensive_generator(*args, **kwargs) -> str:
            offensive = True
            while offensive:
                attempt = gen_func(*args, **kwargs)

                offensive = not check_func(attempt)

                if logging and offensive:
                    print("Got disallowed word match. Trying again!")

            return attempt

        return _inoffensive_generator

    return decorator


def simple_syllable() -> str:
    letters = set(string.ascii_lowercase)
    vowels = {"a", "e", "i", "o", "u"}
    consonants, vowels = [*(letters - vowels)], [*vowels]
    syllable = f"{random.choice(consonants) + random.choice(vowels) + random.choice(consonants)}"
    return syllable


@inoffensive(check_func=check)
def syllables(min_syls=1, max_syls=3, syl_func: Callable[[], str] | None = None) -> str:
    if not isinstance(syl_func, Callable):
        raise TypeError(
            f"No syllable generation function. Expected Callable, got {syl_func=}"
        )

    word = []
    for _ in range(random.randint(min_syls, max_syls)):
        word += [syl_func()]

    return word


def simple_word(min_syls=1, max_syls=3) -> str:
    return "".join(syllables(min_syls, max_syls, syl_func=simple_syllable))


def maybe_punctuated_name(min_syls=1, max_syls=3) -> str:
    if min_syls < 1:
        min_syls = 1
    puncts = ["'", "-"] + [""] * 3
    name = ""
    syls = syllables(min_syls, max_syls, syl_func=simple_syllable)

    for syl in syls[:-1]:
        name += syl + random.choice(puncts)

    return name + syls[-1]
