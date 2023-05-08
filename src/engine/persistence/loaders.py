from src.engine.guild import Guild
from src.entities.action.actions import ActionPoints
from src.entities.combat.archetypes import FighterArchetype
from src.entities.combat.fighter import EncounterContext, Fighter
from src.entities.combat.modifiable_stats import ModifiableStats, Modifier
from src.entities.combat.stats import FighterStats, HealthPool, StatAffix
from src.entities.entity import Entity, Name
from src.entities.item.equipment import Equipment
from src.entities.item.equippable import Equippable, EquippableConfig
from src.entities.item.inventory import Inventory
from src.entities.item.items import HealingPotion
from src.entities.magic.caster import Caster, MpPool
from src.entities.sprite_assignment import Species, attach_sprites


class GameStateLoaders:
    @classmethod
    def guild_from_dict(cls, serialised_guild: dict) -> Guild:
        scalar = serialised_guild.pop("roster_scalar")
        team = serialised_guild.pop("team")

        g = Guild(**serialised_guild)
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
    def entity_from_dict(cls, data: dict | None) -> Entity | None:
        if data is None:
            return None
        instance = Entity()
        instance.__dict__ = {
            **data,
            "name": Name(**data["name"]),
            "fighter": cls.fighter_from_dict(data.get("fighter"), owner=instance),
            "inventory": cls.inventory_from_dict(data.get("inventory"), owner=instance),
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
    def fighter_from_dict(cls, data: dict | None, owner: Entity) -> Fighter | None:
        if data is None:
            return None
        instance = object.__new__(Fighter)
        instance.__dict__ = {
            **data,
            "owner": owner,
            "health": cls.health_pool_from_dict(data.get("health")),
            "stats": FighterStats(**data.get("stats")),
            "equipment": cls.equipment_from_dict(data.get("equipment"), owner=instance),
            "action_points": cls.action_points_from_dict(data.get("action_points")),
            "_caster": cls.caster_from_dict(data=data.get("caster"), owner=instance)
            if data["caster"] is not None
            else None,
            "on_retreat_hooks": [],
            "is_enemy": False,
            "is_boss": False,
            "retreating": False,
            "_in_combat": False,
            "_readied_action": None,
            "_encounter_context": EncounterContext(fighter=instance),
            "role": data["role"],
        }

        instance.role = data.get("role")
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
        instance.equipment.equip_item(instance.equipment.weapon)
        instance.equipment.equip_item(instance.equipment.helmet)
        instance.equipment.equip_item(instance.equipment.body)

        return instance

    @classmethod
    def caster_from_dict(cls, data, owner) -> Caster:
        instance = object.__new__(cls)
        instance.owner = owner
        instance.mp_pool = cls.mp_pool_from_dict(data)

        return instance

    @classmethod
    def mp_pool_from_dict(cls, data) -> MpPool:
        return MpPool(**data["mp_pool"])

    @classmethod
    def health_pool_from_dict(cls, data: dict):
        return HealthPool(**data)

    @classmethod
    def action_points_from_dict(cls, data: dict) -> ActionPoints | None:
        return ActionPoints(data.get("per_turn"))

    @classmethod
    def inventory_from_dict(cls, data, owner) -> Inventory:
        inv = object.__new__(Inventory)
        inv.owner = owner
        items = []
        
        for item in data["items"]:
            if not item:
                items.append(None)
                continue
            
            match item["name"]:
                case "healing potion":
                    item = HealingPotion.from_dict(owner)
                    item.on_add_to_inventory(inv)

        inv.items = items
        inv.capacity = data["capacity"]

        return inv

    @classmethod
    def equipment_from_dict(cls, data: dict, owner: Fighter) -> Equipment | None:
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
        instance = object.__new__(Equipment)

        instance.owner = owner
        instance.weapon = None
        instance.helmet = None
        instance.body = None

        for slot in instance._equippable_slots:
            setattr(
                instance,
                data[slot]["config"]["slot"],
                cls.equippable_from_dict(data[slot], owner=instance),
            )
        return instance

    @classmethod
    def equippable_from_dict(cls, data: dict, owner) -> Equippable:
        mods = []
        for affix in data["config"]["affixes"]:
            if affix.get("modifier").get("stat_class") == "FighterStats":
                mods.append(cls.stat_affix_from_dict(affix))

        instance = object.__new__(Equippable)
        instance.__dict__ = {
            "_owner": owner,
            **{f"_{k}": v for k, v in data["config"].items()},
            "_affixes": mods,
            "_available_attack_cache": [],
            "_available_spell_cache": [],
            "_config": EquippableConfig(**{**data["config"], "affixes": mods}),
        }

        return instance

    @classmethod
    def stat_affix_from_dict(cls, affix_dict) -> StatAffix:
        affix_dict["modifier"].pop("stat_class")
        modifier = Modifier(
            FighterStats,
            **{k: FighterStats(**v) for k, v in affix_dict["modifier"].items()},
        )
        return StatAffix(affix_dict["name"], modifier)
