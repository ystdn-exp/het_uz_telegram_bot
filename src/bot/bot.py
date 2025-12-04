from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from src.core.config import settings


# Initialize Redis connection
redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=False,  # aiogram handles encoding/decoding
)
# FSM storage
storage = RedisStorage(redis=redis)


# Initialize bot instance with default properties
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,  # Use HTML formatting by default
    ),
)

# Initialize dispatcher with storage
dp = Dispatcher(storage=storage)

# router for all handlers
router = Router()

dp.include_router(router)
