import logging

from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.middleware.gzip import GZipMiddleware
from aiogram import types

from src.core.logging_config import init_logging, init_sentry
from src.bot.bot import bot, dp
from src.web.dependencies import verify_telegram_secret, verify_telegram_ip_address


logger = logging.getLogger(__name__)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("Setting up webhook")

#     try:
#         if not settings.WEBHOOK_URL:
#             logger.info("WEBHOOK_URL not set in env. Skipping internal webhook setup.")
#             logger.info("Assuming external service (webhook_setup) will handle it.")
#         else:
#             webhook_info = await bot.get_webhook_info()
#             if webhook_info.url != settings.WEBHOOK_URL:
#                 await bot.set_webhook(
#                     url=settings.WEBHOOK_URL, secret_token=settings.WEBHOOK_SECRET_KEY
#                 )
#                 logger.info(f"Webhook has been successfully set up to {settings.WEBHOOK_URL}")
#             else:
#                 logger.info("Webhook is already set up")
#     except Exception as e:
#         logger.error(f"Failed to check/set webhook: {e}")

#     yield

#     await bot.delete_webhook()
#     await bot.session.close()

#     logger.info("Webhook has been successfully deleted")


app = FastAPI(
    # lifespan=lifespan,
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

    logger.info(
        "Processes: logging, monitoring have been successfully initialized"
    )


# on shutdown
@app.on_event("shutdown")
async def on_shutdown_event():
    await bot.session.close()


@app.get("/healthz", tags=["health"])
async def check_health():
    return {"status": "ok"}


@app.post(
    "/bot/webhook",
    tags=["bot"],
    dependencies=[Depends(verify_telegram_secret), Depends(verify_telegram_ip_address)],
)
async def telegram_webhook(request: Request):
    data = await request.json()
    logger.info(f"Received update: {data}")
    update = types.Update(**data)
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=status.HTTP_200_OK)
