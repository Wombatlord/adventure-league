from random import randint
from typing import Optional
from src.engine.engine import Engine


class Describer:
    def __init__(self) -> None:
        self.owner: Optional[Engine]

    def describe_entrance(self) -> str:
        if self.owner is None:
            raise ValueError("Describer.owner is None. It should never be None if the Engine has been instantiated.")

        dungeon_entrance_messages = [
            f"The {self.owner.guild.team.name} of {self.owner.guild.name} draw their weapons and charge into {self.owner.dungeon.description}!",
            f"The {self.owner.guild.team.name} of {self.owner.guild.name} storm the gates of {self.owner.dungeon.description}!",
            f"The {self.owner.guild.team.name} of {self.owner.guild.name} cry 'Havoc!' and let slip the dogs of war!",
            f"With nerves steeled, the {self.owner.guild.team.name} of {self.owner.guild.name} begin their assault on {self.owner.dungeon.description}!",
            f"Hungry for battle, the {self.owner.guild.team.name} of {self.owner.guild.name} approach {self.owner.dungeon.description}!",
            f"{self.owner.dungeon.description} looms defiant as the {self.owner.guild.team.name} of {self.owner.guild.name} approach!",
            f"Wicked laughter echoes from within {self.owner.dungeon.description} while the {self.owner.guild.team.name} of {self.owner.guild.name} prepare for battle!",
            f"Uneasy silence settles over {self.owner.dungeon.description} before the {self.owner.guild.team.name}' symphony of steel begins!",
            f"Foul odours pour from {self.owner.dungeon.description} as the {self.owner.guild.team.name} of {self.owner.guild.name} cross the threshold!",
            f"Hoisting the banner of {self.owner.guild.name}, the {self.owner.guild.team.name} enter {self.owner.dungeon.description}!"
        ]

        return dungeon_entrance_messages[randint(0, len(dungeon_entrance_messages) - 1)]

    def describe_room_complete(self) -> str:
        if self.owner is None:
            raise ValueError("Describer.owner is None. It should never be None if the Engine has been instantiated.")

        room_complete_messages = [
            f"Splattered with gore, the {self.owner.guild.team.name} move deeper into {self.owner.dungeon.description}!",
            f"With bloodied weapons, the {self.owner.guild.team.name} press onward!",
            f"The {self.owner.guild.team.name} step over the fallen, pushing further into {self.owner.dungeon.description}!",
            f"The {self.owner.guild.team.name} cheer before continuing their assault!",
            f"Jagged teeth leer from the darkness as more enemies arrive and fall upon the {self.owner.guild.team.name}!",
            f"The {self.owner.guild.team.name} win a brief reprieve and gird themselves for further bloodshed!",
            f"The ragged edges of well used iron glint from the shadows of {self.owner.dungeon.description}! The {self.owner.guild.team.name} prepare their steel!",
            f"Heavy footsteps echo from deeper within {self.owner.dungeon.description}!",
            f"With a mortal strike delivered, the {self.owner.guild.team.name} wave the banner of {self.owner.guild.name} before continuing the song of battle!",
            f"The {self.owner.guild.team.name} tighten their armour and charge ahead!"
        ]

        return room_complete_messages[randint(0, len(room_complete_messages) - 1)]
