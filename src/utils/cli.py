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


class HelpCommand(metaclass=CommandMeta):
    name = "help"

    @staticmethod
    def run(*args):
        help_doc = (
            f"------------------------\n"
            f"  Adventure League CLI  \n"
            f"------------------------\n\n"
            f"Available CLI Commands:\n\n"
            f"- debug_commands: Print a dict of available CLI commands. Mostly for development to check commands are registered.\n"
            f"- gen_hashes: Generate hashes from a url resource defined in generate_hashes.py. Write hashes to a file. Used to constrain proc_gen naming.\n"
            f"- archive_assets: Zip and upload the assets folder of the project to GoogleDrive.\n"
            f"- get_assets: Download the assets zip from GoogleDrive. The zip will be found in adventure_league/assets after download.\n\n"
            f"Main Project Commands:\n\n"
            f"- python main.py -m D: run the project in Debug Mode.\n"
            f"- python main.py -m S: run the sprite viewer util."
        )

        print(f"{help_doc}")
