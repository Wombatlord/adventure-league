from typing import Collection, Generic, Self, TypeVar

_StatType = TypeVar("_StatType", bound=tuple)


def namedtuple_add(
    stats_class: type[_StatType], a: _StatType, b: _StatType
) -> _StatType:
    if not isinstance(a, tuple) or not isinstance(a, stats_class):
        raise TypeError(f"The first term {a=} was not of type {stats_class}.")

    if not isinstance(b, a.__class__):
        raise TypeError(
            f"Cannot add {a} of type {a.__class__} to {b} of type {type(b)}"
        )

    args = []
    for self_stat, other_stat in zip(a, b):
        args.append(self_stat + other_stat)

    return stats_class(*args)


class Modifier(Generic[_StatType]):
    _stat_class: type[_StatType]
    _percent: _StatType
    _base: _StatType

    @classmethod
    def from_dict(cls, data) -> Self:
        pass

    def to_dict(self) -> dict:
        return {
            "stat_class": self._stat_class.name,
            "percent": self.percent,
            "base": self.base,
        }

    def __init__(
        self,
        stat_class: type[_StatType],
        percent: _StatType | None = None,
        base: _StatType | None = None,
    ):
        # stat_class validation
        if not hasattr(stat_class, "__add__"):
            raise TypeError(
                f"stat_class must implement __add__. Supplied type {stat_class} has no "
                "__add__ attribute."
            )

        if not issubclass(stat_class, tuple):
            raise TypeError(f"stat_class {stat_class} must be hashable")
        # stat_class is ok!
        self._stat_class = stat_class

        try:
            # the supplied base value change, or the default value of the stats
            self._base = base or stat_class()
            # check: the supplied value must be an instance of stat_class
            if not isinstance(self._base, stat_class):
                raise ValueError(
                    f"The supplied flat modification to the stats {base} was not an instance "
                    f"of the stat class {stat_class}"
                )
            # the supplied percent value change, or the default value of the stats
            self._percent = percent or stat_class()
            # check: the supplied value must be an instance of stat_class
            if not isinstance(self._percent, stat_class):
                raise ValueError(
                    f"The supplied percent modification to the stats {percent} was not an "
                    f"instance of the stat class {stat_class}"
                )

        except TypeError as e:
            # catches the case where the supplied stat_class has positional args with no defaults
            raise TypeError(
                f"The stat class {stat_class} must have default values for all constructor arguments"
            ) from e

    @property
    def base(self) -> int:
        return self._base

    @property
    def percent(self) -> int:
        return self._percent

    def apply(self, base_stats: _StatType) -> _StatType:
        """
        Used to apply this modifier to base stats get the modified stats.

        In the case of multiple modifiers, to apply them properly, use code like the following example:

            >>> mod1 = Modifier(base=Stats(power=1))
            >>> mod2 = Modifier(percent=Stats(power=1))
            >>> base_stats = Stats(power=3, defence=1, speed=3)
            >>> modified_stats = (mod1 + mod2).apply(base_stats)
        """
        modified_stats = {}
        for idx, (name, stat) in enumerate(base_stats._asdict().items()):
            modified_base = stat + self._base[idx]
            percent_change = modified_base * self._percent[idx] / 100

            modified_stats[name] = modified_base + percent_change

        return self._stat_class(**modified_stats)

    def __add__(self, other: Self) -> Self:
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Cannot add {self} of type {self.__class__} to {other} of type {type(other)}"
            )

        return Modifier(
            stat_class=self._stat_class,
            percent=self.percent + other.percent,
            base=self.base + other.base,
        )

    def __radd__(self, other: Self) -> Self:
        return self.__add__(other)

    def __repr__(self) -> str:
        exprs = []
        for idx, key in enumerate(self._base._asdict().keys()):
            stat_name = key
            flat_mod = self._base[idx]
            percent_mod = self._percent[idx]
            exprs.append(
                f"{stat_name} -> ({stat_name} + {flat_mod}) * (100 + {percent_mod})/100"
            )

        details = " | ".join(exprs)

        return f"<{object.__repr__(self)} {details} >"

    def __hash__(self) -> int:
        return hash(self._percent) + hash(self._base)


class ModifiableStats(Generic[_StatType]):
    _stat_class: type[_StatType]
    _base_stats: _StatType
    _modifiers: list[Modifier]

    def __init__(self, stat_class: type[_StatType], base_stats: _StatType):
        self._stat_class = stat_class
        self._base_stats = base_stats
        self._modifiers = [Modifier(self._stat_class)]

    def include_modifier(self, modifier: Modifier[_StatType]):
        self._modifiers.append(modifier)

    def clear_modifiers(self):
        self._modifiers = [Modifier(self._stat_class)]

    def set_modifiers(self, modifiers: Collection[Modifier[_StatType]]):
        self._modifiers = list(modifiers)

    def remove(self, modifier: Modifier[_StatType]) -> bool:
        """
        Removes the first matching modifier instance found in the current modifier stack.
        Will return True if a modifier was removed otherwise False if no removal candidate is found.

        To remove all matching, use a while modifiable_stats.remove(mod) loop
        """
        hashes = [hash(mod) for mod in self._modifiers]
        if (mod_hash := hash(modifier)) in hashes:
            idx = hashes.index(mod_hash)
            self._modifiers.pop(idx)
            return True
        return False

    @property
    def current(self) -> _StatType:
        return sum(self._modifiers, Modifier(self._stat_class)).apply(self._base_stats)
