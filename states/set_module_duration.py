from aiogram.fsm.state import State, StatesGroup


class SetModuleDuration(StatesGroup):
    waiting_for_new_time = State()

