import hashlib
import random
import string

from src.utils.proc_gen.constraints import disallowed


def simple_syllable() -> str:
    letters = set(string.ascii_lowercase)
    vowels = {"a", "e", "i", "o", "u"}
    consonants, vowels = [*(letters - vowels)], [*vowels]
    syllable = f"{random.choice(consonants) + random.choice(vowels) + random.choice(consonants)}"
    return syllable


def syllables(min_syls=1, max_syls=3) -> str:
    word = []
    for _ in range(random.randint(min_syls, max_syls)):
        word += [simple_syllable()]

    for syl in word:
        if syl := inoffensive(syl):
            continue
        else:
            print("BAD SYLLABLE")
            word = syllables()
            return word

    return word


def simple_word(min_syls=1, max_syls=3) -> str:
    return "".join(syllables(min_syls, max_syls))


def maybe_punctuated_name(min_syls=1, max_syls=3) -> str:
    if min_syls < 1:
        min_syls = 1
    puncts = ["'", "-"] + [""] * 3
    name = ""
    syls = syllables(min_syls, max_syls)

    for syl in syls[:-1]:
        name += syl + random.choice(puncts)

    return name + syls[-1]


def inoffensive(name) -> bool:
    as_bytes = str.encode(name)
    hashed = hashlib.sha256(as_bytes)
    if hashed.digest() in disallowed:
        return False
    else:
        return True
