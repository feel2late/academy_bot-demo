from aiogram.fsm.state import State, StatesGroup


class AddLessonDescription(StatesGroup):
    waiting_for_text = State()

class AddModuleDescription(StatesGroup):
    waiting_for_text = State()

class AddCourseDescription(StatesGroup):
    waiting_for_text = State()


