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
    def get_team_with_members(cls, number_of_members: int):
        team = Team()

        for _ in range(number_of_members):
            merc = Entity(
                name=Name(first_name="strong", last_name="very", title="the tactical"),
                fighter=Fighter(**FighterFixtures.strong(enemy=False, boss=False)),
            )
            merc.inventory = Inventory(owner=merc, capacity=1)
            team.assign_to_team(
                merc, True
            )  # Passing True allows us to avoid instantiating an unneeded guild for these tests

        return team

    def test_xp_correctly_sums_and_total_is_granted_to_sole_team_member(self):
        # Arrange
        team = self.get_team_with_members(1)
        exp = Experience(50)
        exp2 = Experience(50)
        loot = Loot()
        loot._team_xp_to_be_awarded.extend([exp, exp2])

        # Action
        loot.claim_team_xp(team)

        # Assert
        assert (
            team.members[0].fighter.leveller.current_xp == 100
        ), f"Experience on leveller should be 100, got: {team.members[0].fighter.leveller.current_xp}"

    def test_xp_correctly_sums_and_splits_between_multiple_team_members(self):
        # Arrange
        team = self.get_team_with_members(2)
        exp = Experience(50)
        exp2 = Experience(50)
        loot = Loot()
        loot._team_xp_to_be_awarded.extend([exp, exp2])

        # Action
        loot.claim_team_xp(team)

        # Assert
        assert (
            team.members[0].fighter.leveller.current_xp == 50
            and team.members[1].fighter.leveller.current_xp == 50
        ), f"Expected both members to have 100: Member 0: {team.members[0].fighter.leveller.current_xp}, Member 1: {team.members[0].fighter.leveller.current_xp}"

    def test_level_up_happens_after_current_xp_hits_level_threshold(self):
        team = self.get_team_with_members(1)
        exp = Experience(999)
        loot = Loot()

        loot._team_xp_to_be_awarded.append(exp)
        loot.claim_team_xp(team)
        assert team.members[0].fighter.leveller.current_xp == 999
        assert team.members[0].fighter.leveller.current_level == 0

        exp = Experience(1)
        loot._team_xp_to_be_awarded.append(exp)
        loot.claim_team_xp(team)

        assert (
            team.members[0].fighter.leveller.current_xp == 0
        ), f"Expected 1000, got: {team.members[0].fighter.leveller.current_xp}"
        assert team.members[0].fighter.leveller.current_level == 1
