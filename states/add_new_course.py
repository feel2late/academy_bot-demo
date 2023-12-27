from aiogram.fsm.state import State, StatesGroup


class AddCourse(StatesGroup):
    title = State()

class AddLesson(StatesGroup):
    title = State()
    description = State()
    
class AddModule(StatesGroup):
    title = State()
    


