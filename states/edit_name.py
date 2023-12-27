from aiogram.fsm.state import State, StatesGroup


class EditLessonName(StatesGroup):
    waiting_for_text = State()

class EditModuleName(StatesGroup):
    waiting_for_text = State()

class EditCourseName(StatesGroup):
    waiting_for_text = State()


