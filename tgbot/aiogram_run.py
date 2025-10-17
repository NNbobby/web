import asyncio
from create_bot import bot, dp
from handlers.start import start_router
from db_handler.db_class import init_db


async def main():
    dp.include_router(start_router)
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())