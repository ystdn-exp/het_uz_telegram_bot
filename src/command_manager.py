import os
import logging

from inspect import getmembers, isclass
from importlib.util import spec_from_file_location, module_from_spec
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from src.core.config import settings


logger = logging.getLogger(__name__)


def default_cmd_path() -> str:
    """
    Helper function to get default commands location.
    """
    default_commands_dir = os.path.join(settings.BASE_DIR, "src", "commands")
    return default_commands_dir


class BaseCommand(ABC):
    """
    Base class for all commands.

    Rules:
    - inherited command class must have name "Command"
    """

    help_text: str = "No help text provided"

    def __init__(self):
        self.options: Dict[str, Any] = {}

    @abstractmethod
    async def handle(self, *args, **options):
        """
        Main command logic.
        Must be implemented by subclasses.
        """
        pass

    def add_argument(self, parser):
        """
        Override this method to add custom arguments
        parser is an argparse.ArgumentParser instance.
        """
        pass

    async def execute(self, *args, **options):
        """Execute the command."""
        self.options = options

        try:
            await self.handle(*args, **options)
        except Exception as e:
            self.on_error(e)
            raise

    def on_error(self, reason: Exception):
        """
        Hook for error handling.
        """
        logger.error("Error executing command: %s", reason)

    def log_success(self, message: str):
        """
        Log success message.
        """
        logger.info("[✓] %s", message)

    def log_error(self, message: str):
        """
        Log error message.
        """
        logger.warning("[✗] %s", message)

    def log_info(self, message: str):
        """
        Log info message.
        """
        logger.info("[ℹ] %s", message)


class CommandManager:
    """
    Manages and executes commands.
    """

    def __init__(self, commands_path: str = default_cmd_path()):
        self.commands_path = Path(commands_path)
        self.commands: Dict[str, type[BaseCommand]] = {}
        self._load_commands()

    def _load_commands(self):
        """
        Automatically discover and load all commands from commands directory.
        """
        if not self.commands_path.exists():
            self.commands_path.mkdir(parents=True, exist_ok=True)

        for file_path in self.commands_path.glob("*.py"):
            # exclude special files e.g. "__init__.py"
            if file_path.name.startswith("_"):
                continue

            command_name = file_path.stem
            self._load_command_from_file(command_name, file_path)

    def _load_command_from_file(self, command_name: str, file_path: Path):
        """
        Load a command from a python file.
        """
        try:
            spec = spec_from_file_location(command_name, file_path)

            if spec and spec.loader:
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

                # find command class in module
                for name, obj in getmembers(module, isclass):
                    if (
                        issubclass(obj, BaseCommand)
                        and obj is not BaseCommand
                        and name == "Command"
                    ):
                        self.commands[command_name] = obj
                        # assume that first declared class is included
                        break
        except Exception as e:
            logger.error("Error loading command %s: %s", command_name, e)

    def register_command(self, name: str, command_class: type[BaseCommand]):
        """
        Manually register command.
        """
        if not issubclass(command_class, BaseCommand):
            raise ValueError("Command must inherit from BaseCommand")

        self.commands[name] = command_class

    async def call_command(self, command_name: str, *args, **options):
        """
        Execute a command by name.
        """
        if command_name not in self.commands:
            raise ValueError(f"Command {command_name} not found")

        command_class = self.commands[command_name]
        command_instance = command_class()
        await command_instance.execute(*args, **options)

    def get_command(self, command_name: str) -> Optional[type[BaseCommand]]:
        """Get command class by name."""
        return self.commands.get(command_name)

    def list_commands(self) -> list[str]:
        """List all registered commands."""
        return list(self.commands.keys())

    def get_help(self, command_name: Optional[str] = None) -> str:
        """Get help text for a command or all commands."""
        if command_name:
            if command_name in self.commands:
                command_cls_instance = self.commands[command_name]()
                return command_cls_instance.help_text

            return f"Command {command_name} not found"

        help_text = "Available commands:\n"
        for name, cmd_class in self.commands.items():
            help_text += f" {name}: {cmd_class().help_text}\n"

        return help_text


command_manager = CommandManager()
