import ipaddress

from fastapi import Header, HTTPException, Request, status

from src.core.config import settings


async def verify_telegram_secret(
    x_telegram_bot_api_secret_token: str = Header(
        alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    if x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret token",
        )


async def verify_telegram_ip_address(request: Request):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For can be a list: "client, proxy1, proxy2"
        # We want the first one.
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-IP") or request.client.host

    try:
        ip = ipaddress.ip_address(client_ip)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid IP address format: {client_ip}",
        )

    # 2. Check against Telegram's CIDR ranges
    for network in settings.TELEGRAM_IP_RANGES:
        if ip in network:
            return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"IP {client_ip} not allowed",
    )
