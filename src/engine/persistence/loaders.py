from src.engine.armory import Armory
from src.engine.guild import Guild
from src.entities.action.actions import ActionPoints
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.fighter import EncounterContext, Fighter
from src.entities.combat.leveller import Leveller
from src.entities.combat.modifiable_stats import ModifiableStats, Modifier
from src.entities.combat.stats import (EquippableItemStats, FighterStats,
                                       HealthPool, StatAffix)
from src.entities.entity import Entity, Name
from src.entities.gear.equippable_item import (EquippableItem,
                                               EquippableItemConfig)
from src.entities.gear.gear import Gear
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.entities.magic.caster import Caster, MpPool
from src.entities.sprite_assignment import Species, attach_sprites
from src.entities.sprites import SimpleSpriteAttribute
from src.gui.simple_sprite_config import choose_item_texture


class GameStateLoaders:
    @classmethod
    def guild_from_dict(cls, serialised_guild: dict) -> Guild:
        scalar = serialised_guild.pop("roster_scalar")
        team = serialised_guild.pop("team")
        armory = serialised_guild.pop("armory")
        g = Guild(**serialised_guild)
        g.armory = cls.armory_from_dict(armory)

        g.team.name = team["name"]

        entities = []
        for e in serialised_guild["roster"]:
            entities.append(cls.entity_from_dict(e))
        g.roster = entities
        for member in team["members"]:
            m = cls.entity_from_dict(member)
            g.team.assign_to_team(m, from_file=True)

        g.roster_scalar = scalar

        return g

    @classmethod
    def armory_from_dict(cls, serialised_armory: dict) -> Armory:
        instance = Armory()
        instance.storage = [
            cls.equippable_item_from_dict(item, None)
            for item in serialised_armory["storage"]
        ]

        return instance

    @classmethod
    def entity_from_dict(cls, serialised_entity: dict | None) -> Entity | None:
        if serialised_entity is None:
            return None
        instance = Entity()
        instance.__dict__ = {
            **serialised_entity,
            "name": Name(**serialised_entity["name"]),
            "fighter": cls.fighter_from_dict(
                serialised_entity.get("fighter"), owner=instance
            ),
            "inventory": cls.inventory_from_dict(
                serialised_entity.get("inventory"), owner=instance
            ),
            "is_dead": False,
            "locatable": None,
            "item": None,
            "ai": None,
            "on_death_hooks": [],
            "species": Species.HUMAN,
            "entity_sprite": None,
        }

        instance = attach_sprites(instance)

        return instance

    @classmethod
    def fighter_from_dict(
        cls, serialised_fighter: dict | None, owner: Entity
    ) -> Fighter | None:
        if serialised_fighter is None:
            return None
        instance = object.__new__(Fighter)
        instance.__dict__ = {
            **serialised_fighter,
            "owner": owner,
            "health": cls.health_pool_from_dict(serialised_fighter.get("health")),
            "leveller": cls.leveller_from_dict(
                serialised_fighter.get("leveller"), owner=instance
            ),
            "stats": FighterStats(**serialised_fighter.get("stats")),
            "gear": cls.gear_from_dict(serialised_fighter.get("gear"), owner=instance),
            "action_points": cls.action_points_from_dict(
                serialised_fighter.get("action_points")
            ),
            "_caster": cls.caster_from_dict(
                serialised_caster=serialised_fighter.get("caster"), owner=instance
            )
            if serialised_fighter["caster"] is not None
            else None,
            "on_retreat_hooks": [],
            "is_enemy": False,
            "is_boss": False,
            "retreating": False,
            "_in_combat": False,
            "_readied_action": None,
            "_encounter_context": EncounterContext(fighter=instance),
            "role": serialised_fighter["role"],
        }

        # We serialise without preceeding underscores,
        # so pop this key from the instance.__dict__ after instantiating the caster
        # under the _caster attribute.
        instance.__dict__.pop("caster")

        instance.role = serialised_fighter.get("role")
        match instance.role:
            case "MELEE":
                instance.set_role(FighterArchetype.MELEE)
            case "RANGED":
                instance.set_role(FighterArchetype.RANGED)
            case "CASTER":
                instance.set_role(FighterArchetype.CASTER)

        instance.set_role(instance.role)
        instance.modifiable_stats = ModifiableStats(
            FighterStats, base_stats=instance.stats
        )

        # Warmup the caches. We do it here because this is when the Fighter has ModifiableStats
        instance.gear.equip_item(instance.gear.weapon)
        instance.gear.equip_item(instance.gear.helmet)
        instance.gear.equip_item(instance.gear.body)

        return instance

    @classmethod
    def leveller_from_dict(cls, serialised_leveller, owner) -> Leveller:
        instance = Leveller(owner)
        instance._current_level = serialised_leveller["current_level"]
        instance._current_xp = serialised_leveller["current_xp"]

        return instance

    @classmethod
    def caster_from_dict(cls, serialised_caster: dict, owner: Fighter) -> Caster:
        instance = object.__new__(Caster)
        instance.owner = owner
        instance.mp_pool = cls.mp_pool_from_dict(serialised_caster)

        return instance

    @classmethod
    def mp_pool_from_dict(cls, serialised_mp_pool: dict) -> MpPool:
        return MpPool(**serialised_mp_pool["mp_pool"])

    @classmethod
    def health_pool_from_dict(cls, serialised_health_pool: dict):
        return HealthPool(**serialised_health_pool)

    @classmethod
    def action_points_from_dict(
        cls, serialised_action_points: dict
    ) -> ActionPoints | None:
        return ActionPoints(serialised_action_points.get("per_turn"))

    @classmethod
    def inventory_from_dict(cls, serialised_inventory, owner) -> Inventory:
        inv = object.__new__(Inventory)
        inv.owner = owner
        items = []

        for item in serialised_inventory["items"]:
            if not item:
                items.append(None)
                continue

            match item["name"]:
                case "healing potion":
                    item = HealingPotion.from_dict(owner)
                    item.on_add_to_inventory(inv)

        inv.items = items
        inv.capacity = serialised_inventory["capacity"]

        return inv

    @classmethod
    def gear_from_dict(cls, serialised_gear: dict, owner: Fighter) -> Gear | None:
        """
        Hydrates an equipment instance with the data dict and attaches the owner.
        Assign slots first so that they exist, then hydrate each equippable from the data dict.
        Equipment.equip_item() should be called on the equippables after the owner has ModifiableStats
        to ensure attack / spell caches are prepared.

        Args:
            data (dict): dict representation of equipment and contained equippables.
            owner (Fighter): owner of this equipment instance.

        Returns:
            Self | None: Equipment containing hydrated equippables.
        """
        instance = object.__new__(Gear)

        instance.owner = owner
        instance._weapon = None
        instance._helmet = None
        instance._body = None
        instance.base_equipped_stats = EquippableItemStats(
            **serialised_gear["base_equipped_stats"]
        )
        instance.modifiable_equipped_stats = ModifiableStats(
            EquippableItemStats, base_stats=instance.base_equipped_stats
        )

        for slot in instance._equippable_slots:
            match slot:
                case "_weapon":
                    instance._weapon = cls.equippable_item_from_dict(
                        serialised_gear[slot], owner=owner
                    )

                case "_helmet":
                    instance._helmet = cls.equippable_item_from_dict(
                        serialised_gear[slot], owner=owner
                    )

                case "_body":
                    instance._body = cls.equippable_item_from_dict(
                        serialised_gear[slot], owner=owner
                    )

        return instance

    @classmethod
    def equippable_item_from_dict(
        cls, serialised_equippable_item: dict | None, owner: Fighter
    ) -> EquippableItem | None:
        if not serialised_equippable_item:
            return None

        fighter_mods = []
        for affix in serialised_equippable_item["config"]["fighter_affixes"]:
            if affix.get("modifier").get("stat_class") == "FighterStats":
                fighter_mods.append(cls.fighter_stat_affix_from_dict(affix))

        equippable_mods = []
        for affix in serialised_equippable_item["config"]["equippable_item_affixes"]:
            if affix.get("modifier").get("stat_class") == "EquippableStats":
                equippable_mods.append(cls.equippable_item_stat_affix_from_dict(affix))

        instance = object.__new__(EquippableItem)
        instance.__dict__ = {
            "_owner": owner,
            **{f"_{k}": v for k, v in serialised_equippable_item["config"].items()},
            "_fighter_affixes": fighter_mods,
            "_equippable_item_affixes": equippable_mods,
            "_available_attack_cache": [],
            "_available_spell_cache": [],
            "_stats": EquippableItemStats(**serialised_equippable_item["stats"]),
            "_config": EquippableItemConfig(
                **{
                    **serialised_equippable_item["config"],
                    "fighter_affixes": fighter_mods,
                    "equippable_item_affixes": equippable_mods,
                }
            ),
        }

        instance._sprite = SimpleSpriteAttribute(
            path_or_texture=choose_item_texture(instance), scale=6
        )
        instance._sprite.owner = instance

        instance._modifiable_stats = ModifiableStats(
            EquippableItemStats, instance._stats
        )

        return instance

    @classmethod
    def fighter_stat_affix_from_dict(cls, serialised_stat_affix: dict) -> StatAffix:
        serialised_stat_affix["modifier"].pop("stat_class")
        modifier = Modifier(
            FighterStats,
            **{
                k: FighterStats(**v)
                for k, v in serialised_stat_affix["modifier"].items()
            },
        )
        return StatAffix(serialised_stat_affix["name"], modifier)

    @classmethod
    def equippable_item_stat_affix_from_dict(
        cls, serialised_stat_affix: dict
    ) -> StatAffix:
        serialised_stat_affix["modifier"].pop("stat_class")
        modifier = Modifier(
            EquippableItemStats,
            **{
                k: EquippableItemStats(**v)
                for k, v in serialised_stat_affix["modifier"].items()
            },
        )
        return StatAffix(serialised_stat_affix["name"], modifier)
