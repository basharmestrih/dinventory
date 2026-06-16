import asyncio
import logging
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher

from app.bot_commands import setup_bot_commands
from app.config import settings
from app.routers import register_routers
from app.webhook import create_zeno_webhook_app


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    webhook_handler = logging.FileHandler(logs_dir / "webhooks.log", encoding="utf-8")
    webhook_handler.setLevel(logging.INFO)
    webhook_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

    for logger_name in ("app.webhook", "app.services.webhooks.zeno_webhook", "app.services.webhooks.fawaterk_webhook"):
        webhook_logger = logging.getLogger(logger_name)
        webhook_logger.setLevel(logging.INFO)
        webhook_logger.addHandler(webhook_handler)


async def start_bot() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    webhook_runner: web.AppRunner | None = None

    register_routers(dp)
    await setup_bot_commands(bot)

    try:
        if settings.zeno_webhook_enabled:
            webhook_runner = web.AppRunner(create_zeno_webhook_app(bot))
            await webhook_runner.setup()
            site = web.TCPSite(
                webhook_runner,
                host=settings.zeno_webhook_host,
                port=settings.zeno_webhook_port,
            )
            await site.start()
            logging.getLogger(__name__).info(
                "Zeno webhook server listening on http://%s:%s/webhooks/zeno",
                settings.zeno_webhook_host,
                settings.zeno_webhook_port,
            )

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if webhook_runner is not None:
            await webhook_runner.cleanup()


def run() -> None:
    setup_logging()
    asyncio.run(start_bot())
