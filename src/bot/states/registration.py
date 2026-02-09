"""
FSM states for bot workflows.
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for HET account registration flow."""

    waiting_for_username = State()
    waiting_for_password = State()
