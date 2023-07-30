from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Callable, Generator, NamedTuple

from src.engine.events_enum import EventFields, EventTopic
from src.entities.entity import Entity
from src.entities.gear.equippable_item import EquippableItem
from src.entities.item.equippable_item import body, bow, get_item_configs, helmet
from src.entities.item.loot import Loot
from src.world.level.dungeon import Dungeon

if TYPE_CHECKING:
    from src.engine.engine import Engine


class ItemRollParams(NamedTuple):
    is_boss: bool = False
    is_enemy: bool = True

    @classmethod
    def from_entity(cls, entity: Entity):
        return cls(
            is_boss=entity.fighter.is_boss,
            is_enemy=entity.fighter.is_enemy,
        )


class DropConfig:
    _table: dict[ItemRollParams, Generator[EquippableItem, None, None]]

    def __init__(self, table: dict) -> None:
        self._table = table

    def __getitem__(
        self, params: ItemRollParams
    ) -> Generator[EquippableItem, None, None]:
        drops = self._table.get(params, (_ for _ in range(0)))
        yield from drops


def roll_slot(slot: str = None) -> Callable[[], EquippableItem | None]:
    configs = get_item_configs().items_where(lambda item: item.slot == slot)
    rewards = [
        EquippableItem(owner=None, config=item_config) for item_config in configs
    ]
    if not rewards:
        rewards = [None]
    return lambda: random.choice(rewards)


def roll_boss_table():
    yield from roll_table(
        [
            (80000, []),
            (5, [body]),
            (5, [helmet] * 2),
            (1, [bow] * 3),
        ]
    )
    yield from roll_table(
        [
            (1, []),
            (1, roll_boss_table()),
        ]
    )


def roll_table(table):
    roll = random.randrange(0, sum(*[rate for rate, _ in table]))
    while drop := table.pop(0):
        rate, rewards = drop
        if rate > roll:
            yield from (reward for reward in rewards)
        else:
            roll -= rate


common_item_drops = DropConfig(
    {
        ItemRollParams(is_boss=True): (
            roll() for roll in [roll_slot("_weapon"), roll_slot("_helmet")]
        ),
        ItemRollParams(): (roll() for roll in [roll_slot("_body")]),
        ItemRollParams(is_enemy=False): roll_boss_table(),
    }
)


class ItemDropListener:
    topic = EventTopic.ROLL_ITEM_DROP
    current_encounter: Dungeon | None = None
    tables = [common_item_drops]

    @classmethod
    def update_encounter(cls, event: dict):
        cls.current_encounter = event.get(EventTopic.COMBAT_START, {}).get(
            EventFields.DUNGEON
        )

    @classmethod
    def clear_encounter(cls, event: dict):
        if EventTopic.CLEANUP in event:
            cls.current_encounter = None

    @classmethod
    def handle(cls, event: dict) -> Any:
        if not cls.current_encounter:
            return
        loot: Loot = cls.current_encounter.loot
        source: Entity = event[EventTopic.ROLL_ITEM_DROP]
        roll_params = ItemRollParams.from_entity(source)
        for drops in cls.tables:
            loot.item_drops.extend(
                (item for item in drops[roll_params] if item is not None)
            )


def subscribe(eng: Engine):
    eng.static_subscribe(
        topic=EventTopic.COMBAT_START,
        handler_id=f"{ItemDropListener.__name__}.set_encounter",
        handler=ItemDropListener.update_encounter,
    )

    eng.static_subscribe(
        topic=EventTopic.CLEANUP,
        handler_id=f"{ItemDropListener.__name__}.clear_encounter",
        handler=ItemDropListener.clear_encounter,
    )

    eng.static_subscribe(
        topic=ItemDropListener.topic,
        handler_id=f"{ItemDropListener.__name__}.handle",
        handler=ItemDropListener.handle,
    )
