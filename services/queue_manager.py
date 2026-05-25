import asyncio
import logging
from typing import Callable, Awaitable, Any, Dict
from aiogram.exceptions import TelegramRetryAfter

class UniversalQueue:
    def __init__(self, bot, send_delay: float = 0.35, check_delay: float = 1.0):
        self.bot = bot
        self.send_delay = send_delay
        self.check_delay = check_delay
        self.message_queues: Dict[int, asyncio.Queue] = {}
        self.check_queues: Dict[int, asyncio.Queue] = {}
        self.workers = {}

    def ensure_workers(self, chat_id: int):
        if chat_id not in self.message_queues:
            self.message_queues[chat_id] = asyncio.Queue()
            self.workers[f"msg_{chat_id}"] = asyncio.create_task(self._message_worker(chat_id))
        if chat_id not in self.check_queues:
            self.check_queues[chat_id] = asyncio.Queue()
            self.workers[f"chk_{chat_id}"] = asyncio.create_task(self._check_worker(chat_id))

    async def _message_worker(self, chat_id: int):
        q = self.message_queues[chat_id]
        while True:
            kwargs = await q.get()
            try:
                if 'photo' in kwargs: await self.bot.send_photo(chat_id, **kwargs)
                else: await self.bot.send_message(chat_id, **kwargs)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                if 'photo' in kwargs: await self.bot.send_photo(chat_id, **kwargs)
                else: await self.bot.send_message(chat_id, **kwargs)
            except Exception as e: logging.error(f"Ошибка отправки в чат {chat_id}: {e}")
            finally: await asyncio.sleep(self.send_delay)

    async def _check_worker(self, chat_id: int):
        q = self.check_queues[chat_id]
        while True:
            coro = await q.get()
            try:
                if chat_id in self.message_queues:
                    while not self.message_queues[chat_id].empty(): await asyncio.sleep(0.5)
                await coro
            except Exception as e: logging.error(f"Ошибка проверки чата {chat_id}: {e}")
            finally: await asyncio.sleep(self.check_delay)

    def enqueue_message(self, chat_id: int, text: str = None, **kwargs):
        self.ensure_workers(chat_id)
        if text: kwargs['text'] = text
        self.message_queues[chat_id].put_nowait(kwargs)

    def enqueue_check(self, chat_id: int, coro: Callable[[], Awaitable[Any]]):
        self.ensure_workers(chat_id)
        self.check_queues[chat_id].put_nowait(coro)
