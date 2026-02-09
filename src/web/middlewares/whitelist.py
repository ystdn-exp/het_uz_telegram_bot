import ipaddress

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.config import settings


class TelegramIPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        client_ip = ipaddress.ip_address(request.client.host)
        allowed = any(client_ip in net for net in settings.TELEGRAM_IP_RANGES)

        if not allowed:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied: not a Telegram IP"},
            )
        return await call_next(request)
