from random import choice

class Describer:
    @staticmethod
    def describe_entrance(eng) -> str:

        dungeon_entrance_messages = [
            f"The {eng.game_state.guild.team.name} of {eng.game_state.guild.name} draw their weapons and charge into {eng.game_state.dungeon.description}!",
            f"The {eng.game_state.guild.team.name} of {eng.game_state.guild.name} storm the gates of {eng.game_state.dungeon.description}!",
            f"The {eng.game_state.guild.team.name} of {eng.game_state.guild.name} cry 'Havoc!' and let slip the dogs of war!",
            f"With nerves steeled, the {eng.game_state.guild.team.name} of {eng.game_state.guild.name} begin their assault on {eng.game_state.dungeon.description}!",
            f"Hungry for battle, the {eng.game_state.guild.team.name} of {eng.game_state.guild.name} approach {eng.game_state.dungeon.description}!",
            f"{eng.game_state.dungeon.description} looms defiant as the {eng.game_state.guild.team.name} of {eng.game_state.guild.name} approach!",
            f"Wicked laughter echoes from within {eng.game_state.dungeon.description} while the {eng.game_state.guild.team.name} of {eng.game_state.guild.name} prepare for battle!",
            f"Uneasy silence settles over {eng.game_state.dungeon.description} before the {eng.game_state.guild.team.name}' symphony of steel begins!",
            f"Foul odours pour from {eng.game_state.dungeon.description} as the {eng.game_state.guild.team.name} of {eng.game_state.guild.name} cross the threshold!",
            f"Hoisting the banner of {eng.game_state.guild.name}, the {eng.game_state.guild.team.name} enter {eng.game_state.dungeon.description}!"
        ]

        return choice(dungeon_entrance_messages)

    def describe_room_complete(eng) -> str:

        room_complete_messages = [
            f"Splattered with gore, the {eng.game_state.guild.team.name} move deeper into {eng.game_state.dungeon.description}!",
            f"With bloodied weapons, the {eng.game_state.guild.team.name} press onward!",
            f"The {eng.game_state.guild.team.name} step over the fallen, pushing further into {eng.game_state.dungeon.description}!",
            f"The {eng.game_state.guild.team.name} cheer before continuing their assault!",
            f"Jagged teeth leer from the darkness as more enemies arrive and fall upon the {eng.game_state.guild.team.name}!",
            f"The {eng.game_state.guild.team.name} win a brief reprieve and gird themselves for further bloodshed!",
            f"The ragged edges of well used iron glint from the shadows of {eng.game_state.dungeon.description}! The {eng.game_state.guild.team.name} prepare their steel!",
            f"Heavy footsteps echo from deeper within {eng.game_state.dungeon.description}!",
            f"With a mortal strike delivered, the {eng.game_state.guild.team.name} wave the banner of {eng.game_state.guild.name} before continuing the song of battle!",
            f"The {eng.game_state.guild.team.name} tighten their armour and charge ahead!"
        ]

        return choice(room_complete_messages)
