class FighterFixtures:
    @staticmethod
    def strong(enemy=False, boss=False):
        return {
            "hp": 100,
            "defence": 10,
            "power": 10,
            "is_enemy": enemy,
            "speed": 1,
            "is_boss": boss,
        }

    @staticmethod
    def baby(enemy=False, boss=False):
        return {
            "hp": 1,
            "defence": 0,
            "power": 0,
            "is_enemy": enemy,
            "speed": 1,
            "is_boss": boss,
        }
