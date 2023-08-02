import os
import sys

from src.tools import registered_tools

os.environ["DEBUG"] = "1"


def main(args: list[str]):
    args = args or [""]
    command_name = args.pop(0)
    print(f"Attempting to find subcommand {command_name}")
    command = subcommands.get(command_name, print_help)
    command(args)


def run(args: list[str]):
    tool_name = args.pop()
    print(f"Attempting to run {tool_name}")
    tool = registered_tools.get(tool_name, list_tools)
    tool(args)


def list_tools(args: list[str]):
    print("Tools available (by tool name):")
    print("\n".join(registered_tools.keys()))
    print()
    print("To use a tool, run the following:")
    print("python tools.py run {tool name}")


def print_help(args: list[str]):
    print("Subcommands available:")
    print("\n".join(subcommands.keys()))
    print()
    print("To use a subcommand, run the following:")
    print("python tools.py {subcommand} {subcommand args}")


subcommands = {"run": run, "list": list_tools, "help": print_help}

if __name__ == "__main__":
    main(sys.argv[1:])
