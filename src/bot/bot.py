import httpx
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from src.bot.handlers import language, register, start, users
from src.bot.middlewares.auth import AuthMiddleware
from src.bot.middlewares.localization import LocaleMiddleware
from src.bot.middlewares.logging import LoggingMiddleware
from src.bot.middlewares.session import DbSessionMiddleware
from src.core.config import settings
from src.database.connection import session_pool

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
bot.session_client = httpx.AsyncClient(timeout=httpx.Timeout(20.0))

# Initialize dispatcher with storage
dp = Dispatcher(storage=storage)

# register middlewares
dp.update.outer_middleware(LoggingMiddleware())
dp.update.outer_middleware(DbSessionMiddleware(session_pool=session_pool))
dp.update.outer_middleware(AuthMiddleware())
dp.update.outer_middleware(LocaleMiddleware())

router = Router()

# Register all handlers
router.include_router(start.router)
router.include_router(language.router)
router.include_router(register.router)
router.include_router(users.router)

dp.include_router(router)
