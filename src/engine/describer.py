from random import choice

class Describer:
    @staticmethod
    def describe_entrance(eng) -> str:

        dungeon_entrance_messages = [
            f"The {eng.guild.team.name} of {eng.guild.name} draw their weapons and charge into {eng.dungeon.description}!",
            f"The {eng.guild.team.name} of {eng.guild.name} storm the gates of {eng.dungeon.description}!",
            f"The {eng.guild.team.name} of {eng.guild.name} cry 'Havoc!' and let slip the dogs of war!",
            f"With nerves steeled, the {eng.guild.team.name} of {eng.guild.name} begin their assault on {eng.dungeon.description}!",
            f"Hungry for battle, the {eng.guild.team.name} of {eng.guild.name} approach {eng.dungeon.description}!",
            f"{eng.dungeon.description} looms defiant as the {eng.guild.team.name} of {eng.guild.name} approach!",
            f"Wicked laughter echoes from within {eng.dungeon.description} while the {eng.guild.team.name} of {eng.guild.name} prepare for battle!",
            f"Uneasy silence settles over {eng.dungeon.description} before the {eng.guild.team.name}' symphony of steel begins!",
            f"Foul odours pour from {eng.dungeon.description} as the {eng.guild.team.name} of {eng.guild.name} cross the threshold!",
            f"Hoisting the banner of {eng.guild.name}, the {eng.guild.team.name} enter {eng.dungeon.description}!"
        ]

        return choice(dungeon_entrance_messages)

    def describe_room_complete(eng) -> str:

        room_complete_messages = [
            f"Splattered with gore, the {eng.guild.team.name} move deeper into {eng.dungeon.description}!",
            f"With bloodied weapons, the {eng.guild.team.name} press onward!",
            f"The {eng.guild.team.name} step over the fallen, pushing further into {eng.dungeon.description}!",
            f"The {eng.guild.team.name} cheer before continuing their assault!",
            f"Jagged teeth leer from the darkness as more enemies arrive and fall upon the {eng.guild.team.name}!",
            f"The {eng.guild.team.name} win a brief reprieve and gird themselves for further bloodshed!",
            f"The ragged edges of well used iron glint from the shadows of {eng.dungeon.description}! The {eng.guild.team.name} prepare their steel!",
            f"Heavy footsteps echo from deeper within {eng.dungeon.description}!",
            f"With a mortal strike delivered, the {eng.guild.team.name} wave the banner of {eng.guild.name} before continuing the song of battle!",
            f"The {eng.guild.team.name} tighten their armour and charge ahead!"
        ]

        return choice(room_complete_messages)
