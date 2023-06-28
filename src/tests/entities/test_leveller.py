import unittest

from src.engine.guild import Guild, Team
from src.entities.combat.fighter import Fighter
from src.entities.combat.leveller import Experience
from src.entities.entity import Entity, Name
from src.entities.item.inventory import Inventory
from src.entities.item.loot import Loot
from src.tests.fixtures import FighterFixtures


class LevellerTest(unittest.TestCase):
    @classmethod
    def get_team_with_single_member(cls):
        team = Team()
        merc = Entity(
            name=Name(first_name="strong", last_name="very", title="the tactical"),
            fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
        )
        merc.inventory = Inventory(owner=merc, capacity=1)
        team.assign_to_team(merc, True) # Passing True allows us to avoid instantiating an unneeded guild for these tests

        return team

    def test_xp_correctly_sums_and_total_is_granted_to_sole_team_member(self):
        team = self.get_team_with_single_member()
        exp = Experience(50)
        exp2 = Experience(50)
        loot = Loot()
        loot.team_xp.extend([exp, exp2])

        loot.claim_team_xp(team)

        assert (
            team.members[0].fighter.leveller.current_xp == 100
        ), f"Experience on leveller should be 100, got: {team.members[0].fighter.leveller.current_xp}"
