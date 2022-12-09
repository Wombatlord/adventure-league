
class Rewarder:
    def claim_gp(self) -> int:
        raise NotImplementedError()

    def claim_xp(self) -> int:
        raise NotImplementedError()
        
class Loot(Rewarder):
    xp: int
    gp: int
    _text: str

    def __init__(
        self,
        xp=0,
        gp=0,
    ):
        self.xp = max(0, xp)
        self.gp = max(0, gp)

        
    @property
    def claimed(self) -> bool:
        return self.xp == 0 and self.gp == 0

    def claim_gp(self) -> int:
        gp, self.gp = self.gp, 0
        return gp

    def claim_xp(self) -> int:
        xp, self.xp = self.xp, 0
        return xp

    def __str__(self) -> str:
        if self.claimed:
            return "This reward has already been claimed"

        return f"XP: {self.xp}, GP: {self.gp}"
    
