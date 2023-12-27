import asyncio
from aiogram import Dispatcher
import aioschedule
from bot_init import bot
import db_requests
import datetime
from handlers import start, menu, admin_menu, bot_settings, cancel, course, module, lesson, delete_additional_materials
from middlewares.outer import MigrateChat


async def main():
    dp = Dispatcher()
    dp.include_routers(start.router, menu.router, bot_settings.router, admin_menu.router, cancel.router, course.router, module.router, 
                       lesson.router, delete_additional_materials.router)
    dp.message.outer_middleware(MigrateChat())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())