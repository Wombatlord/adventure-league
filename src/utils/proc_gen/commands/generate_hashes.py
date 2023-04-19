import hashlib
import pathlib

import requests
import string
import src

from src.utils.cli import CommandMeta
from src.utils.proc_gen.constraints import keep_allowed

project_root = pathlib.Path(src.__file__).parent.parent
urls = [
    "http://www.bannedwordlist.com/lists/swearWords.txt",
]

def from_url(url) -> list[bytes]:
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to locate resource at" + response.request.url)
        return

    wordlist = response.content.split(b"\n")
    allowed_chars = string.ascii_lowercase + " "


    return [keep_allowed(w.decode().lower().encode(), allowed_chars) for w in wordlist]


def merge_lists():
    words: set[bytes] = {b"verbotenharam"}
    for url in urls:
        words |= set(from_url(url))

    to_file(list(words))


def to_file(wordlist: list[bytes]):
    hashes = b"".join(
        map(
            lambda line: hashlib.sha256(line).digest(),
            wordlist,
        )
    )

    target_path = project_root / "assets" / "wordlists" / "hashes.bin"

    try:
        write_hashes(hashes, target_path)

    except FileNotFoundError:
        target_path.parent.mkdir()
        write_hashes(hashes, target_path)

    print(f"Wrote {len(wordlist)} hashes to hashes.bin")

def write_hashes(hashes, target_path):
    with open(target_path, "wb") as outfile:
        outfile.write(hashes)

class Command(metaclass=CommandMeta):
    name = "gen_hashes"
    @staticmethod
    def run(*args):
        merge_lists()