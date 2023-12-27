from aiogram.fsm.state import State, StatesGroup


class AddHomework(StatesGroup):
    waiting_for_text = State()


class AddTeachersComment(StatesGroup):
    waiting_for_text = State()


