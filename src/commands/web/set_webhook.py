from typer import Typer

from src.core.config import settings


command = Typer()


@command.command()
def set_bot_webhook():
    pass
