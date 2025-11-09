"""
CLI runner for management commands

Usage:
    python manage.py <command_name> [options]
    python mmanage.py --list
    python manage.py --help <command_name>
"""

import argparse
import asyncio
import sys

from src.command_manager import command_manager


def main():
    parser = argparse.ArgumentParser(
        description="Management command runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--list", action="store_true", help="List all available commands")

    parser.add_argument("command", nargs="?", help="Command to run")

    parser.add_argument("args", nargs="*", help="Command arguments")

    args, unknown = parser.parse_known_args()

    # List commands
    if args.list:
        print("Available commands:")
        print(command_manager.get_help())
        return

    if not args.command:
        parser.print_help()
        return

    command_name = args.command
    if command_name not in command_manager.list_commands():
        print(f"Error: Command '{command_name}' not found")
        print(f"\nAvailable commands: {', '.join(command_manager.list_commands())}")
        sys.exit(1)

    # Parse command-specific arguments
    cmd_class = command_manager.get_command(command_name)
    if cmd_class:
        cmd_parser = argparse.ArgumentParser(description=cmd_class().help_text)

        cmd_instance = cmd_class()
        cmd_instance.add_arguments(cmd_parser)

        cmd_args = cmd_parser.parse_args(unknown)
        options = vars(cmd_args)

        print(f"Executing command: {command_name}")
        print("-" * 50)

        try:
            asyncio.run(command_manager.call_command(command_name, **options))
            print("-" * 50)
            print(f"✓ Command '{command_name}' completed successfully")
        except Exception as e:
            print("-" * 50)
            print(f"✗ Error executing command: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
