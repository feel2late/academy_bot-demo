import asyncio
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot_init import bot
import db_requests


class MigrateChat(BaseMiddleware):
    """Отлавливает апдейт на изменение ID чата (например, при миграции в супергруппу) и изменяет ID чата в БД"""
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        migrate_from_chat_id = data.get('event_update').message.migrate_from_chat_id
        new_chat_id = data.get('event_update').message.chat.id
        if migrate_from_chat_id:
            message_text = ('⚠️ Внимание! Вы изменили тип группы, а следовательно удалилась инвайт-ссылка для учеников и изменился ID группы.\n\n'
                            'Вам необходимо:\n1) Установить тип группы "Приватная"\n2) Удалить и добавить меня заново, чтобы провести настройку.')
            await bot.send_message(new_chat_id, message_text)
        
        return await handler(event, data)

