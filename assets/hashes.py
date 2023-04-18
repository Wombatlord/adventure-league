import hashlib
import pathlib

import requests

urls = [
    "http://www.bannedwordlist.com/lists/swearWords.txt",
]


def from_url(url) -> list[bytes]:
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to locate resource at" + response.request.url)
        return

    wordlist = response.content.split()

    return wordlist

def merge_lists():
    words: set[bytes] = set()
    for url in urls:
        words = set(from_url(url))

    to_file(list(words))


def to_file(wordlist: list[bytes]):
    hashes = b"".join(
        map(
            lambda line: hashlib.sha256(line).digest(),
            wordlist,
        )
    )

    target_path = pathlib.Path(__file__).parent / "wordlists" / "hashes.bin"
    
    try:
        with open(target_path, "wb") as outfile:
            outfile.write(hashes)
    
    except FileNotFoundError:
        parent = pathlib.Path(__file__).parent
        pathlib.Path(f"{parent}/wordlists").mkdir()

        with open(target_path, "wb") as outfile:
            outfile.write(hashes)
        
    print(f"Wrote {len(wordlist)} hashes to hashes.bin")


if __name__ == "__main__":
    merge_lists()
