from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.guild import Team

from src.entities.combat.leveller import Experience


class Rewarder:
    def claim_gp(self) -> int:
        raise NotImplementedError()

    def claim_guild_xp(self) -> int:
        raise NotImplementedError()


class Loot(Rewarder):
    guild_xp: int
    team_xp: list[Experience]
    gp: int
    _text: str

    def __init__(
        self,
        xp=0,
        gp=0,
    ):
        self.guild_xp = max(0, xp)
        self.gp = max(0, gp)
        self.team_xp = []

    @property
    def claimed(self) -> bool:
        return self.guild_xp == 0 and self.gp == 0

    def claim_gp(self) -> int:
        gp, self.gp = self.gp, 0
        return gp

    def claim_guild_xp(self) -> int:
        xp, self.guild_xp = self.guild_xp, 0
        return xp

    def claim_team_xp(self, team: Team):
        member_count = len(team.members)

        final = Experience(0)
        for experience in self.team_xp:
            final += experience

        final = final // member_count

        for member in team.members:
            member.fighter.leveller.gain_exp(final)

    def team_xp_total(self) -> int:
        total = Experience(0)
        for xp in self.team_xp:
            total += xp
        return total.xp_value

    def __str__(self) -> str:
        if self.claimed:
            return "This reward has already been claimed"

        return f"XP: {self.guild_xp}, GP: {self.gp}"
