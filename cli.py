import sys
from src.utils.cli import commands
from src.utils.proc_gen.commands.generate_hashes import Command as _


if __name__ == "__main__":
    cmd = commands.get(sys.argv[1])
    if cmd is None:
        raise ValueError(f"Command {sys.argv[1]} not found. Available commands: {[*commands.keys()]}")

    cmd.run(*sys.argv[1:])
