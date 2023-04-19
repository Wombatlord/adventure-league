import hashlib
import string

HashList = list[bytes]


def get_hashes() -> HashList:
    target_path = "./assets/wordlists/hashes.bin"
    with open(target_path, "rb") as hashfile:
        hashes = hashfile.read()

        hashlist = [hashes[i : i + 32] for i in range(0, len(hashes), 32)]

    return hashlist


_disallowed_list = []


def load():
    global _disallowed_list
    _disallowed_list = get_hashes()


def sanitize_char(text: str, char: str) -> bytes:
    return b"".join([substr.encode() for substr in text.split(char)])


def keep_allowed(text: bytes, allowed_chars: str) -> bytes:
    text_str = text.decode()
    to_remove = set(text_str) - set(allowed_chars)
    result = text
    for removal in to_remove:
        result = sanitize_char(result.decode(), removal)

    return result


def check(s: str, disallowed_hashes: HashList | None = None) -> bool:
    global _disallowed_list

    if disallowed_hashes is None:
        disallowed_hashes = _disallowed_list

    sanitized_token = keep_allowed(
        "".join(s).lower().encode(), string.ascii_lowercase + " "
    )

    return allowed_token(sanitized_token, disallowed_hashes)


def allowed_token(token: bytes, disallowed_hashes: HashList) -> bool:
    hashed = hashlib.sha256(token)

    if hashed.digest() in disallowed_hashes:
        return False
    else:
        return True
