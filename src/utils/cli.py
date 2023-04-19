commands = {}


class CommandMeta(type):
    def __new__(cls, *args, **kwargs):
        command_class = super().__new__(cls, *args, **kwargs)

        if command_class.name in commands:
            raise KeyError(f"Name Collision on {command_class.name=}")

        commands[command_class.name] = command_class

        return command_class


class Command(metaclass=CommandMeta):
    name = "debug_commands"

    @staticmethod
    def run(*args):
        print(commands)
