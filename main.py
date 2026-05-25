import asyncio
import logging
from loader import bot, dp

from handlers.users import user_router
from handlers.admin import admin_router
from handlers.groups import group_router

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(group_router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен. Очереди сообщений активны.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
