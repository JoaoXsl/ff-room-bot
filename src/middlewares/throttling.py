from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from cachetools import TTLCache

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, time_limit: int = 2) -> None:
        self.cache = TTLCache(maxsize=10000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        if user_id in self.cache:
            return await event.answer("⚠️ Por favor, não envie comandos tão rápido!")

        self.cache[user_id] = True
        return await handler(event, data)
