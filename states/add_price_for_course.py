from aiogram.fsm.state import State, StatesGroup


class AddPriceForCourse(StatesGroup):
    waiting_for_new_price = State()

