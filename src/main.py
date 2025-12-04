import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.middleware.gzip import GZipMiddleware
from aiogram import types

from src.core.config import settings
from src.core.logging_config import init_logging, init_sentry
from src.bot.bot import bot, dp
from src.core.scheduler import init_scheduler, shutdown_scheduler
from src.bot.bot import bot
from src.web.dependencies import verify_telegram_secret, verify_telegram_ip_address


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Setting up webhook")

    webhook_info = bot.get_webhook_info()
    if webhook_info.url != settings.WEBHOOK_URL:
        await bot.set_webhook(
            url=settings.WEBHOOK_URL, secret_token=settings.WEBHOOK_SECRET_KEY
        )
        logger.info("Webhook has been successfully set up")
    else:
        logger.info("Webhook is already set up")

    yield

    bot.delete_webhook()
    bot.session.close()

    logger.info("Webhook has been successfully deleted")


app = FastAPI(
    lifespan=lifespan,
    title="Telegram bot HET with webhook",
    docs_url="/docs",
    redoc_url="/redoc",
)

# register all midllewares here
app.add_middleware(GZipMiddleware, minimum_size=1024)


# on startup
@app.on_event("startup")
async def on_startup_event():
    init_logging()
    init_sentry()
    init_scheduler()

    logger.info(
        "Processes: logging, monitoring and scheduler have been successfully initialized"
    )


# on shutdown
@app.on_event("shutdown")
async def on_shutdown_event():
    shutdown_scheduler()
    logger.info("Scheduler has been successfully disabled")

    bot.session.close()


@app.get("/healthz", tags=["health"])
async def check_health():
    return {"status": "ok"}


@app.post(
    "/bot/webhook",
    tags=["bot"],
    dependencies=[Depends(verify_telegram_secret, verify_telegram_ip_address)],
)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=status.HTTP_200_OK)
