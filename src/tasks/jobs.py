"""
Scheduled jobs.
"""

import logging

import redis.asyncio as aioredis

from src.bot.bot import bot
from src.bot.utils.context_variables import i18n
from src.core.config import settings
from src.database.connection import session_pool
from src.database.models.users import UserInTelegramUser
from src.services.het import het_service
from src.services.users import TelegramUserService

redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", decode_responses=True
)


logger = logging.getLogger(__name__)


async def daily_task():
    """
    Daily task to send consumption reports to all users.
    """
    logger.info("Daily task started")

    try:
        async with session_pool() as session:
            users = await TelegramUserService.get_all_users(session)

            for telegram_user in users:
                if not telegram_user.users:
                    continue

                try:
                    # Set locale for this user
                    lang = telegram_user.language or "en"
                    _ = i18n.get_translations(lang).gettext

                    report_lines = [_("📊 <b>Daily Usage Report</b>")]
                    has_data = False

                    # Pre-fetch account data to avoid async expiration issues after commit
                    accounts_data = []
                    for link in telegram_user.users:
                        accounts_data.append(
                            {
                                "id": link.id,
                                "username": link.user.username,
                                "access_token": link.access_token,
                                "refresh_token": link.refresh_token,
                            }
                        )

                    for acc in accounts_data:
                        try:
                            # Try to get data
                            access_token = acc["access_token"]
                            refresh_token = acc["refresh_token"]
                            username = acc["username"]

                            data, status = await het_service.get_consumer_state(
                                bot.session_client, access_token
                            )

                            # Handle 401 (Refresh Token) if needed
                            if status == 401 and refresh_token:
                                logger.info(f"Refreshing token for user {username}")
                                (
                                    new_tokens,
                                    cls_status,
                                ) = await het_service.refresh_token(
                                    bot.session_client, refresh_token
                                )

                                if cls_status == 200 and new_tokens.get("data"):
                                    # Update tokens in DB
                                    tokens = new_tokens["data"]
                                    new_access = tokens.get("accessToken")
                                    new_refresh = tokens.get("refreshToken")

                                    link_obj = await session.get(
                                        UserInTelegramUser, acc["id"]
                                    )
                                    if link_obj:
                                        link_obj.access_token = new_access
                                        link_obj.refresh_token = new_refresh
                                        session.add(link_obj)
                                        await session.commit()

                                        # Update local var for retry
                                        access_token = new_access

                                    # Retry fetch
                                    data, status = await het_service.get_consumer_state(
                                        bot.session_client, access_token
                                    )

                            if status == 200 and data.get("data"):
                                item = data["data"]

                                # Extract info (adjust keys as per real API)
                                balance = item.get("balance")
                                consumption = item.get("daily_consumption") or item.get(
                                    "usage"
                                )

                                info = f"\n👤 <b>{username}</b>"
                                if balance is not None:
                                    display_balance = float(balance) / 100
                                    formatted_balance = "{:,.2f}".format(
                                        display_balance
                                    ).replace(",", " ")
                                    info += (
                                        f"\n💰 {_('Balance')}: {formatted_balance} UZS"
                                    )
                                if consumption is not None:
                                    info += f"\n⚡️ {_('Usage')}: {consumption}"

                                report_lines.append(info)
                                has_data = True

                        except Exception as e:
                            logger.error(
                                f"Error processing account {acc['username']}: {e}"
                            )
                            continue

                    if has_data:
                        await bot.send_message(
                            chat_id=telegram_user.chat_id, text="\n".join(report_lines)
                        )

                except Exception as e:
                    logger.error(
                        f"Error sending daily report to {telegram_user.chat_id}: {e}"
                    )
                    continue

    except Exception as e:
        logger.error(f"Critical error in daily_task: {e}")

    logger.info("Daily task finished")


async def _check_single_account_balance(session, telegram_user, link, _):
    """Helper to check balance for a single account link."""
    try:
        access_token = link.access_token
        data, status = await het_service.get_consumer_state(
            bot.session_client, access_token
        )

        # Handle expired token
        if status == 401 and link.refresh_token:
            new_tokens, refresh_status = await het_service.refresh_token(
                bot.session_client, link.refresh_token
            )
            if refresh_status == 200 and new_tokens.get("data"):
                tokens = new_tokens["data"]
                link.access_token = tokens.get("accessToken")
                link.refresh_token = tokens.get("refreshToken")
                session.add(link)
                await session.commit()
                access_token = link.access_token
                # Retry fetch
                data, status = await het_service.get_consumer_state(
                    bot.session_client, access_token
                )

        if status == 200 and data.get("data"):
            item = data["data"]
            balance = item.get("balance")

            redis_key = f"low_balance_alert:{link.id}"
            if balance is not None and balance < 10000:
                # Up to 3 times
                alert_count = await redis_client.get(redis_key)
                alert_count = int(alert_count) if alert_count else 0

                if alert_count < 3:
                    username = link.user.username
                    display_balance = float(balance) / 100
                    formatted_balance = "{:,.2f}".format(display_balance).replace(
                        ",", " "
                    )
                    msg = str(
                        _(
                            "⚠️ <b>Low Balance Alert!</b>\n\n"
                            "👤 <b>Account:</b> {username}\n"
                            "💰 <b>Current Balance:</b> {balance} UZS\n\n"
                            "Please top up your account to avoid service interruption! ⚡️"
                        )
                    ).format(username=username, balance=formatted_balance)

                    try:
                        await bot.send_message(chat_id=telegram_user.chat_id, text=msg)
                        await redis_client.set(
                            redis_key, str(alert_count + 1), ex=86400 * 7
                        )
                        logger.info(
                            f"Sent low balance alert ({alert_count + 1}/3) to {telegram_user.chat_id} for {username}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to send alert to {telegram_user.chat_id}: {e}"
                        )
            else:
                # Reset if balance is ok
                await redis_client.delete(redis_key)

    except Exception as e:
        logger.error(f"Error checking balance for account {link.id}: {e}")


async def check_low_balances_task():
    """
    Task to check for low balances (< 10,000 UZS) and notify users.
    Runs every hour.
    """
    logger.info("Checking low balances...")
    try:
        async with session_pool() as session:
            users = await TelegramUserService.get_all_users(session)

            for telegram_user in users:
                if not telegram_user.users:
                    continue

                lang = telegram_user.language or "en"
                _ = i18n.get_translations(lang).gettext

                for link in telegram_user.users:
                    await _check_single_account_balance(session, telegram_user, link, _)

    except Exception as e:
        logger.error(f"Critical error in check_low_balances_task: {e}")
