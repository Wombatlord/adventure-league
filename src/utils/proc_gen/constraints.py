import hashlib

HashList = list[bytes]

def get_hashes() -> HashList:
    target_path = "./assets/wordlists/hashes.bin"
    with open(target_path, "rb") as hashfile:
        hashes = hashfile.read()

        hashlist = [hashes[i : i + 32] for i in range(0, len(hashes), 32)]

    return hashlist


_disallowed_list = get_hashes()


def check(s: str, disallowed_hashes: HashList | None = None) -> bool:
    global _disallowed_list

    if disallowed_hashes is None:
        disallowed_hashes = _disallowed_list

    combined = "".join(s)
    final = combined.lower()

    return allowed_token(final, disallowed_hashes)


def allowed_token(token: str, disallowed_hashes: HashList) -> bool:
    as_bytes = str.encode(token)
    hashed = hashlib.sha256(as_bytes)

    if hashed.digest() in disallowed_hashes:
        return False
    else:
        return True
