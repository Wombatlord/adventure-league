class Leveller:
    def __init__(self, owner) -> None:
        self.owner = owner
        self._current_level = 0
        self._current_exp = 0
        self._exp_to_level_up = 1000
    
    @property
    def current_level(self) -> int:
        return self._current_level
    
    @property
    def current_exp(self) -> int:
        return self._current_exp
        
    def increase_level(self):
        self._current_level += 1
    
    def gain_exp(self, amount: int):
        self._current_exp += amount
