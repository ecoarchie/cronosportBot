import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot.handlers.admin import (
    register_admin,
    register_add_race_info,
    register_get_races_list,
    register_delete_race_from_db,
)
from tgbot.handlers.echo import register_echo
from tgbot.handlers.user import (
    register_user,
    register_user_follow_race,
    redister_searh_results,
)
from tgbot.middlewares.db import DbMiddleware
from tgbot.models.sqlitedb import (
    create_tables,
    update_copernico_db,
)

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
scheduler.add_job(update_copernico_db, "interval", seconds=30)


def register_all_middlewares(dp):
    dp.setup_middleware(DbMiddleware())


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)
    register_add_race_info(dp)
    register_user_follow_race(dp)
    register_get_races_list(dp)
    register_delete_race_from_db(dp)
    redister_searh_results(dp)

    register_echo(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u"%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger.info("Starting bot")
    config = load_config(".env")

    if config.tg_bot.use_redis:
        storage = RedisStorage()
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=storage)

    bot["config"] = config

    register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)

    scheduler.start()
    # start
    try:
        await create_tables()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
