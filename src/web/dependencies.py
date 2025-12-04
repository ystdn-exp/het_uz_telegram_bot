from fastapi import Header, HTTPException, status

from src.main import app


async def verify_telegram_secret(
    x_telegram_bot_api_secret_token: str = Header(
        alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    if x_telegram_bot_api_secret_token != app.settings.WEBHOOK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret token",
        )


async def verify_telegram_ip_address(
    x_real_ip: str = Header(alias="X-Real-IP"),
):
    if x_real_ip not in app.settings.TELEGRAM_WHITELIST_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid IP address",
        )
