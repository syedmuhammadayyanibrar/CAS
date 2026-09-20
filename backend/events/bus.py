import asyncio
from typing import Callable, Awaitable, Dict, List
from backend.models.cas_message import CASMessage
from backend.core.logging import get_logger

logger = get_logger("EventBus")

MessageHandler = Callable[[CASMessage], Awaitable[None]]


class CASEventBus:
    """
    Asynchronous event bus facilitating standardized CASMessage passing
    across autonomous societies, the CAS Director, and Fastn adapters.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[MessageHandler]] = {}
        self._global_subscribers: List[MessageHandler] = []

    def subscribe(self, event_type: str, handler: MessageHandler):
        """Subscribes an async handler to a specific CAS event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to event: {event_type}")

    def subscribe_all(self, handler: MessageHandler):
        """Subscribes a handler to all CAS messages (e.g. audit logger, Director)."""
        self._global_subscribers.append(handler)

    async def publish(self, message: CASMessage):
        """Publishes a CASMessage asynchronously to all relevant subscribers."""
        logger.info(
            f"CASMessage Published: [Event: {message.event_type}, "
            f"Source: {message.source_system} -> Target: {message.target_system}, "
            f"Contract: {message.contract_id}, Priority: {message.priority}]"
        )

        handlers = list(self._global_subscribers)
        if message.event_type in self._subscribers:
            handlers.extend(self._subscribers[message.event_type])

        # Execute all handlers concurrently without crashing the bus if one fails
        tasks = []
        for handler in handlers:
            tasks.append(self._safe_execute(handler, message))

        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_execute(self, handler: MessageHandler, message: CASMessage):
        try:
            await handler(message)
        except Exception as e:
            logger.error(f"Error in message handler {handler.__name__} for event {message.event_type}: {e}", exc_info=True)


event_bus = CASEventBus()
