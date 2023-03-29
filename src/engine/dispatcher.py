import weakref
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from src.engine.engine import Engine

from src import config

Handler = Callable[[dict], None]
HandlerRef = Callable[[], Handler]


class Dispatcher:
    def __init__(self, engine: "Engine") -> None:
        self.subscriptions: dict[str, dict[str, HandlerRef]] = {}
        self.eng = engine

    def subscribe(
        self,
        topic: str,
        handler_id: str,
        handler: "Handler",
        is_method=True,
        keep_ref=False,
    ):
        if config.DEBUG:
            print(f"{handler_id=} subscribed with {self.__class__} to {topic=}")

        if not callable(handler):
            raise TypeError(f"A non-callable {type(handler)=} was passed to subscribe")

        # check the subscription is a new one
        subs = {}
        if topic in self.subscriptions and handler_id in (
            subs := self.subscriptions[topic]
        ):
            ref = self.subscriptions[topic][handler_id]
            # ignore sub if the topic is already subscribed by that handler
            if ref() is not None:
                return

        # IMPORTANT: we use a weakref to make sure we don't retain subscriptions
        # from components that would otherwise be garbage collected.
        if is_method and not keep_ref:
            handler_ref = weakref.WeakMethod(handler)
        else:
            handler_ref = lambda: handler
        self.subscriptions[topic] = {**subs, handler_id: handler_ref}

    def publish(self, event: dict[str, Any]) -> None:
        if config.DEBUG:
            print(f"{self=} dispatching {event}")
        self._handle_subscriptions(event)

    def _handle_subscriptions(self, event: dict[str, Any]) -> None:
        # print(self.subscriptions)
        for topic in event.keys():
            subscribers = self.subscriptions.get(topic, {})

            living_subs = {}
            for subscriber_id, subscriber_ref in subscribers.items():
                # Dereference the weakref, none if garbage collected
                subscriber = subscriber_ref()

                # since the subscriber is only a weakref, it might be stale, we handle that below
                if subscriber is not None:
                    # This is the case where the instance that owns the handler has strong refs
                    # still kicking about, so we can keep the ref/id pair in the remaining subs for the
                    # topic.
                    living_subs[subscriber_id] = subscriber_ref
                    subscriber(event)
            # Actually replace the subscribers with the ones that remain after collection of garbage
            self.subscriptions[topic] = living_subs

    def flush_subs(self):
        if config.DEBUG:
            print(f"{self.__class__} flushed")
        self.subscriptions: dict[str, dict[str, HandlerRef]] = {}


class VolatileDispatcher(Dispatcher):
    def volatile_subscribe(self, topic: str, handler_id: str, handler: "Handler"):
        self.subscribe(topic, handler_id, handler)


class StaticDispatcher(Dispatcher):
    def static_subscribe(self, topic: str, handler_id: str, handler: "Handler"):
        self.subscribe(topic, handler_id, handler, keep_ref=True)
