from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from services.queue_manager import UniversalQueue

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
queue_manager = UniversalQueue(bot, send_delay=1.0, check_delay=1.0)
