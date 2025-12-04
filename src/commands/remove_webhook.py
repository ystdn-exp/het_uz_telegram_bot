import logging
import requests

from src.core.config import settings
from src.command_manager import BaseCommand


logger = logging.getLogger(__name__)


class SetWebhookCommand(BaseCommand):
    help_text = "Set webhook for bot"

    def add_argument(self, parser):
        parser.add_argument("webhook_url", type=str, help="Webhook URL")

    async def handle(self, *args, **options):
        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setWebhook"
        data = {
            "url": options["webhook_url"],
            "secret_token": settings.WEBHOOK_SECRET_TOKEN,
        }
        response = requests.post(url, data=data)

        if response.status_code == 200:
            logger.info("Webhook set successfully")
        else:
            logger.error(f"Failed to set webhook: {response.text}")
