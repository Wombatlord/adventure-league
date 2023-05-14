from copy import deepcopy
from random import randint
from typing import Callable, NamedTuple

from src.config.constants import merc_names
from src.entities.ai.ai import BasicCombatAi
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.fighter import Fighter
from src.entities.entity import Entity, Name, Species
from src.entities.gear.gear_factory import default_equippable_item_factory
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.entities.magic.caster import Caster
from src.entities.sprite_assignment import attach_sprites
from src.utils.proc_gen import syllables

NAME_GENS: dict[str, Callable[[], str]] = {
    Species.GOBLIN: lambda: (
        f"{syllables.maybe_punctuated_name(max_syls=2)} {syllables.maybe_punctuated_name(max_syls=2)}"
    ),
    Species.SLIME: lambda: f"{syllables.simple_word(max_syls=2)}",
}


def gen_name(species: str) -> str:
    return NAME_GENS.get(species, lambda: f"{species}: '{syllables.simple_word()}'")()


Factory = Callable[[str], Entity]


class StatBlock(NamedTuple):
    hp: tuple[int, int]
    defence: tuple[int, int]
    power: tuple[int, int]
    is_enemy: bool
    speed: int
    role: FighterArchetype = FighterArchetype.MELEE
    is_boss: bool = False
    species: str = "human"

    @property
    def factory(self) -> Factory:
        return get_fighter_factory(self)

    def fighter_conf(self) -> dict:
        return {
            "hp": randint(*self.hp),
            "defence": randint(*self.defence),
            "power": randint(*self.power),
            "is_enemy": self.is_enemy,
            "role": self.role,
            "speed": self.speed,
            "is_boss": self.is_boss,
        }


_melee_mercenary_base = StatBlock(
    hp=(45, 45),
    defence=(3, 5),
    power=(3, 5),
    speed=3,
    role=FighterArchetype.MELEE,
    is_enemy=False,
    is_boss=False,
)
_ranged_mercenary_base = StatBlock(
    hp=(40, 40),
    defence=(1, 3),
    power=(3, 5),
    speed=3,
    role=FighterArchetype.RANGED,
    is_enemy=False,
    is_boss=False,
)
_caster_mercenary_base = StatBlock(
    hp=(45, 45),
    defence=(1, 3),
    power=(2, 4),
    speed=3,
    role=FighterArchetype.CASTER,
    is_enemy=False,
    is_boss=False,
)


_monster = StatBlock(
    species=Species.SLIME,
    hp=(10, 15),
    defence=(1, 3),
    power=(1, 3),
    speed=1,
    is_enemy=True,
    is_boss=False,
)
_goblin = StatBlock(
    species=Species.GOBLIN,
    hp=(15, 20),
    defence=(1, 3),
    power=(2, 4),
    speed=2,
    is_enemy=True,
    is_boss=False,
)
_boss = StatBlock(
    hp=(50, 60),
    defence=(2, 4),
    power=(2, 4),
    speed=1,
    is_enemy=True,
    is_boss=True,
)


def _setup_fighter_archetypes(
    fighter: Fighter, gear_factory: Callable[[FighterArchetype], dict]
):
    def default_equip(fighter: Fighter):
        nonlocal gear
        for slot in fighter.gear._equippable_slots:
            fighter.gear.equip_item(gear.get(slot))

    match fighter.role:
        case FighterArchetype.MELEE:
            gear = gear_factory(FighterArchetype.MELEE)
            default_equip(fighter)

        case FighterArchetype.RANGED:
            gear = gear_factory(FighterArchetype.RANGED)
            default_equip(fighter)

        case FighterArchetype.CASTER:
            fighter.caster = Caster(max_mp=15)
            gear = gear_factory(FighterArchetype.CASTER)
            default_equip(fighter)

    fighter.set_action_options()


def get_fighter_factory(
    stats: StatBlock, should_attach_sprites: bool = True
) -> Factory:
    def _from_conf(fighter_conf: dict, entity: Entity) -> Fighter:
        return Fighter(**fighter_conf).set_owner(owner=entity)

    def _create_entity(first_name, title, last_name) -> Entity:
        return Entity(
            name=Name(title=title, first_name=first_name, last_name=last_name),
            cost=randint(1, 5),
            species=stats.species,
        )

    def factory(name=None, title=None, last_name=None):
        name = name or gen_name(stats.species)
        entity = _create_entity(name, title, last_name)

        conf = stats.fighter_conf()

        entity.fighter = _from_conf(conf, entity)
        gear_factory = default_equippable_item_factory()
        _setup_fighter_archetypes(entity.fighter, gear_factory)

        entity.inventory = Inventory(owner=entity, capacity=1)

        if not entity.fighter.is_enemy:
            entity.inventory.add_item_to_inventory(HealingPotion(owner=entity))
        else:
            entity.ai = BasicCombatAi()

        if should_attach_sprites:
            entity = attach_sprites(entity)

        return entity

    return factory


create_random_melee_fighter = _melee_mercenary_base.factory
create_random_ranged_fighter = _ranged_mercenary_base.factory
create_random_caster_fighter = _caster_mercenary_base.factory
create_random_monster = _monster.factory
create_random_goblin = _goblin.factory
create_random_boss = _boss.factory


class RecruitmentPool:
    def __init__(self, size: int = None) -> None:
        self.size = size
        self.pool: list[Entity] = []

    def increase_pool_size(self, new_size: int) -> None:
        # Set the new pool size and clear the previous pool
        self.size = new_size
        self.pool = []
        # Refill the pool with new recruits
        if self.size <= len(merc_names):
            self.fill_pool()

        else:
            raise ValueError(
                f"Not enough names for recruits. size: {self.size} < names: {len(merc_names)}"
            )

    def fill_pool(self) -> None:
        # Create a deepcopy of name array for consuming with pop.
        name_choices = deepcopy(merc_names)

        for _ in range(self.size):
            # iteratively pop a random name from the deepcopy array and supply the name to the factory.
            name = name_choices.pop(randint(0, len(name_choices) - 1))
            match randint(0, 2):
                case 0:
                    self.pool.append(create_random_melee_fighter(name))
                case 1:
                    self.pool.append(create_random_ranged_fighter(name))
                case 2:
                    self.pool.append(create_random_caster_fighter(name))

            # self.pool.append(create_random_fighter(name))

    def show_pool(self) -> None:
        # Sanity check function
        print(self.pool)
        for i in self.pool:
            print(i.fighter.health.current)
