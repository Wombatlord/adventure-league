from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.guild import Team
    from src.entities.gear.equippable_item import EquippableItem

from src.entities.combat.leveller import Experience


class Rewarder:
    def claim_gp(self) -> int:
        raise NotImplementedError()

    def claim_guild_xp(self) -> int:
        raise NotImplementedError()


class Loot(Rewarder):
    guild_xp: int
    _team_xp_to_be_awarded: list[Experience]
    gp: int
    _text: str
    item_drops: list[EquippableItem]

    def __init__(
        self,
        xp=0,
        gp=0,
    ):
        self.guild_xp = max(0, xp)
        self.gp = max(0, gp)
        self._team_xp_to_be_awarded = []
        self.awarded_xp_per_member = 0
        self.item_drops = []

    @property
    def claimed(self) -> bool:
        return self.guild_xp == 0 and self.gp == 0

    def claim_gp(self) -> int:
        gp, self.gp = self.gp, 0
        return gp

    def claim_guild_xp(self) -> int:
        xp, self.guild_xp = self.guild_xp, 0
        return xp

    def claim_items(self) -> list[EquippableItem]:
        items, self.item_drops = self.item_drops, []
        return items

    def claim_team_xp(self, team: Team):
        member_count = len(team.members)

        final = self.calculate_xp_per_member(member_count)

        for member in team.members:
            member.fighter.leveller.gain_xp(final)

            if member.fighter.leveller.should_level_up():
                member.fighter.leveller._do_level_up()

        self.awarded_xp_per_member = final.xp_value
        self._team_xp_to_be_awarded = []

    def calculate_xp_per_member(self, member_count) -> Experience:
        final = Experience(0)
        for experience in self._team_xp_to_be_awarded:
            final += experience

        final = final // member_count
        return final

    def team_xp_total(self, team: Team) -> int:
        return self.awarded_xp_per_member * len(team.members)

    def __str__(self) -> str:
        if self.claimed:
            return "This reward has already been claimed"

        return f"XP: {self.guild_xp}, GP: {self.gp}"
